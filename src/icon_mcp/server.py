"""MCP 服务器核心 - 注册工具并处理 MCP 协议。"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    CallToolResult,
)

from .config import ServerConfig
from .lang import t, init_from_env
from .models import SelectionStatus
from .utils.cache import CacheManager
from .utils.search import IconSearcher
from .utils.saver import IconSaver
from .utils.web_server import WebServer
from .web.interface import WebInterface


class MCPIconServer:
    """MCP 图标服务器主类 - 协调所有组件。"""

    def __init__(self, config: ServerConfig | None = None):
        self.config = config or ServerConfig()

        # 初始化语言
        init_from_env()

        # 初始化组件
        self.cache = CacheManager(expiry_seconds=self.config.cache_expiry_seconds)
        self.searcher = IconSearcher(self.config, self.cache)
        self.saver = IconSaver(self.cache)
        self.web_server = WebServer(
            cache=self.cache,
            port=self.config.web_server_port,
            auto_open=self.config.web_server_auto_open,
        )
        self.web_interface = WebInterface(port=self.config.web_server_port)
        self.web_server.set_html_generator(self.web_interface)

        # MCP 服务器实例
        self.mcp = Server("icon-mcp-server")
        self._register_handlers()

    def _register_handlers(self) -> None:
        """注册所有 MCP 工具处理器。"""

        @self.mcp.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="search_icons",
                    description=t("search.searchDescription"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "q": {
                                "type": "string",
                                "description": "图标搜索关键词",
                            },
                            "sortType": {
                                "type": "string",
                                "description": "排序方式：recommend（默认）、updated_at",
                                "default": "recommend",
                            },
                            "page": {
                                "type": "integer",
                                "description": "页码（默认：1）",
                                "default": 1,
                                "minimum": 1,
                            },
                            "pageSize": {
                                "type": "integer",
                                "description": "每页结果数（1-100，默认：100）",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 100,
                            },
                        },
                        "required": ["q"],
                    },
                ),
                Tool(
                    name="start_web_server",
                    description=t("web.startServer"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "integer",
                                "description": "服务器端口（默认：3000）",
                            },
                            "autoOpen": {
                                "type": "boolean",
                                "description": "自动打开浏览器（默认：true）",
                                "default": True,
                            },
                        },
                    },
                ),
                Tool(
                    name="stop_web_server",
                    description=t("web.stopServer"),
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="check_selection_status",
                    description=t("web.checkSelection"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "searchId": {
                                "type": "string",
                                "description": "要检查选择状态的搜索 ID",
                            },
                            "maxWaitTime": {
                                "type": "integer",
                                "description": "最大等待时间（毫秒，默认：180000）",
                                "default": 180000,
                            },
                        },
                        "required": ["searchId"],
                    },
                ),
                Tool(
                    name="get_cache_stats",
                    description=t("cache.statsDescription"),
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="clear_cache",
                    description=t("cache.clearDescription"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expiredOnly": {
                                "type": "boolean",
                                "description": "仅清除过期条目（默认：false）",
                                "default": False,
                            },
                        },
                    },
                ),
                Tool(
                    name="save_icons",
                    description="将选中的图标保存为 svg/png/bmp/ico 文件到本地",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "icons": {
                                "type": "array",
                                "description": "要保存的图标对象数组",
                                "items": {"type": "object"},
                            },
                            "savePath": {
                                "type": "string",
                                "description": "图标保存路径（默认：./saved-icons）",
                                "default": "./saved-icons",
                            },
                            "format": {
                                "type": "string",
                                "description": "图标文件格式（默认：svg）。栅格格式会将 SVG 转为像素图。",
                                "enum": ["svg", "png", "bmp", "ico"],
                                "default": "svg",
                            },
                            "size": {
                                "type": "integer",
                                "description": "栅格格式 png/bmp/ico 的像素尺寸（默认：128）",
                                "default": 128,
                            },
                        },
                        "required": ["icons"],
                    },
                ),
            ]

        @self.mcp.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            try:
                result = await self._dispatch_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)}, ensure_ascii=False),
                    )
                ]

    async def _dispatch_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """将工具调用分发给对应的处理器。"""
        if name == "search_icons":
            result = await self.searcher.search_icons(
                q=args.get("q", ""),
                sort_type=args.get("sortType", "recommend"),
                page=args.get("page", 1),
                page_size=args.get("pageSize", 100),
            )
            # 自动启动 Web 服务器（若未运行）
            if not self.web_server.is_running():
                await self.web_server.start(auto_open=False)
                self.web_interface.port = self.web_server.port
                print(f"  Web 服务器已自动启动: {self.web_server.get_url()}", file=sys.stderr)

            search_id = result["search_id"]
            web_url = f"{self.web_server.get_url()}?searchId={search_id}"

            # 面向 LLM 的精简返回：URL 与下一步指引放在最前，icons 只保留
            # 名称，避免完整 SVG 把 URL 淹没导致 LLM 看不到地址。
            # （Web 界面走 /api/cache 读的是另一份完整缓存，不受影响。）
            return {
                "message": (
                    f"已搜索到 {result['count']} 个图标。"
                    f"请让用户在浏览器打开下面的地址挑选图标：\n{web_url}\n"
                    f"用户选好后，调用 check_selection_status 工具"
                    f"（searchId={search_id}）轮询，即可自动拿到选中结果。"
                ),
                "web_url": web_url,
                "search_id": search_id,
                "count": result["count"],
                "total_count": result.get("total_count"),
                "page": result.get("page"),
                "icons": [
                    ic.get("name", f"icon-{ic.get('id')}")
                    for ic in result.get("icons", [])
                ],
            }

        elif name == "start_web_server":
            result = await self.web_server.start(
                port=args.get("port"),
                auto_open=args.get("autoOpen", True),
            )
            self.web_interface.port = self.web_server.port
            return result

        elif name == "stop_web_server":
            return await self.web_server.stop()

        elif name == "check_selection_status":
            return await self._check_selection(
                search_id=args["searchId"],
                max_wait_ms=args.get("maxWaitTime", 180000),
            )

        elif name == "get_cache_stats":
            return self.cache.get_stats()

        elif name == "clear_cache":
            expired_only = args.get("expiredOnly", False)
            result = self.cache.clear(expired_only=expired_only)
            result["message"] = (
                t("cache.expiredCleared") if expired_only else t("cache.cleared")
            )
            return result

        elif name == "save_icons":
            return await self.saver.save_icons(
                icons=args.get("icons", []),
                save_path=args.get("savePath", "./saved-icons"),
                fmt=args.get("format", "svg"),
                size=args.get("size", 128),
            )

        else:
            raise ValueError(t("error.methodNotFound", {"method": name}))

    async def _check_selection(
        self, search_id: str, max_wait_ms: int = 180000
    ) -> dict[str, Any]:
        """轮询用户选择状态，超时则返回。"""
        # 验证 search_id 是否存在
        cached = self.cache.get_search(search_id)
        if cached is None:
            raise ValueError(t("selection.noSearchFound", {"searchId": search_id}))

        print(
            t("selection.checkingStatus", {"searchId": search_id}),
            file=sys.stderr,
        )

        max_wait_s = max_wait_ms / 1000.0
        start = time.time()
        check_interval = 0.1  # 100ms 轮询间隔
        log_interval = 10.0
        last_log = start

        while time.time() - start < max_wait_s:
            selection = self.cache.get_selection(search_id)

            if selection is not None:
                if selection.status == SelectionStatus.COMPLETED:
                    # 清理并返回图标
                    icons = selection.selected_icons
                    self.cache.delete_selection(search_id)
                    return {
                        "success": True,
                        "status": "completed",
                        "selected_icons": icons,
                        "count": len(icons),
                    }
                elif selection.status == SelectionStatus.FAILED:
                    self.cache.delete_selection(search_id)
                    return {
                        "success": False,
                        "status": "failed",
                        "message": t("selection.selectionFailed"),
                    }

            # 定期状态日志
            now = time.time()
            if now - last_log >= log_interval:
                elapsed = int(now - start)
                print(
                    t("selection.waitingForSelection") + f" ({elapsed}s)",
                    file=sys.stderr,
                )
                last_log = now

            await asyncio.sleep(check_interval)

        # 超时
        elapsed = int(time.time() - start)
        return {
            "success": False,
            "status": "timeout",
            "message": t("selection.selectionTimeout", {"seconds": elapsed}),
        }

    async def _auto_test_search(self, query: str) -> None:
        """自动执行搜索并打开 Web 页面，用于 --test 参数测试。"""
        print(f"\n  [测试模式] 自动搜索: {query}", file=sys.stderr)

        try:
            # 确保 Web 服务器已启动
            if not self.web_server.is_running():
                await self.web_server.start(auto_open=False)
                self.web_interface.port = self.web_server.port
                print(f"  Web 服务器已启动: {self.web_server.get_url()}", file=sys.stderr)

            # 执行搜索
            result = await self.searcher.search_icons(q=query, page_size=20)
            search_id = result["search_id"]
            web_url = f"{self.web_server.get_url()}?searchId={search_id}"

            # 输出搜索摘要
            icons = result.get("icons", [])
            total = result.get("total_count", 0)
            print(f"  搜索完成: 本页 {len(icons)} 个图标，总计 {total} 个", file=sys.stderr)
            print(f"  搜索 ID: {search_id}", file=sys.stderr)
            print(f"\n  >>> 浏览器访问: {web_url}", file=sys.stderr)

            # 自动打开浏览器
            self.web_server._open_browser(web_url)

        except Exception as e:
            print(f"  自动搜索失败: {e}", file=sys.stderr)

    async def _cleanup(self) -> None:
        """清理所有资源。"""
        await self.searcher.close()
        if self.web_server.is_running():
            await self.web_server.stop()

    async def run(self) -> None:
        """通过 stdio 运行 MCP 服务器。"""
        print(t("server.starting"), file=sys.stderr)
        print(f"  MCP 传输方式   : stdio", file=sys.stderr)
        print(f"  Web 服务器端口 : {self.config.web_server_port}", file=sys.stderr)
        print(f"  语言           : {self.config.language}", file=sys.stderr)
        print(f"  自动启动 Web   : {self.config.auto_start_web_server}", file=sys.stderr)
        print(f"  自动打开浏览器 : {self.config.web_server_auto_open}", file=sys.stderr)

        # 如已配置则自动启动 Web 服务器
        if self.config.auto_start_web_server:
            await self.web_server.start(auto_open=self.config.web_server_auto_open)
            self.web_interface.port = self.web_server.port
            print(f"  Web 服务器 URL : {self.web_server.get_url()}", file=sys.stderr)

        print(t("server.started"), file=sys.stderr)

        # 测试模式：自动搜索并打开 Web 页面
        if self.config.test_query:
            asyncio.ensure_future(self._auto_test_search(self.config.test_query))

        # 在运行的事件循环上注册信号处理器。
        # add_signal_handler 在 Windows (ProactorEventLoop) 上未实现，
        # 因此跳过注册，依赖 KeyboardInterrupt 处理。
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig, lambda: asyncio.ensure_future(self._shutdown_and_exit())
                )
            except NotImplementedError:
                pass

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp.run(
                    read_stream,
                    write_stream,
                    self.mcp.create_initialization_options(),
                )
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()

    async def _shutdown_and_exit(self) -> None:
        """清理资源后终止进程。

        MCP SDK 的 stdio_server 在阻塞线程中读取 stdin，
        在 macOS 上无法通过任务取消或 fd 关闭来中断。
        清理完成后，将信号处理器重置为默认并重新触发 SIGINT，
        使进程被操作系统正常终止。
        这允许父进程（如 uv）干净地回收子进程，不会出现 ESRCH 错误。
        """
        print(t("server.shutdown"), file=sys.stderr)
        await self._cleanup()
        # 重置为默认处理器并重新触发 — 操作系统终止进程，
        # 父进程可以 waitpid() 而不会出现 ESRCH。
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
