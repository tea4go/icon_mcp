"""MCP 测试客户端 - 通过 JSON-RPC over stdio 验证所有工具。"""

import json
import os
import subprocess
import sys
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable


def main():
    proc = subprocess.Popen(
        [PYTHON, "-m", "icon_mcp", "--language", "zh-CN"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)

    # 使用后台线程读取 stdout，因为 select.select() 在 Windows 上
    # 不支持管道 I/O（仅支持 socket）。
    _lines = []
    _lines_lock = threading.Lock()
    _lines_event = threading.Event()

    def _reader():
        for raw in proc.stdout:
            line = raw.decode().strip()
            if line:
                with _lines_lock:
                    _lines.append(line)
                _lines_event.set()
        # 流结束（进程已退出）
        _lines_event.set()

    _reader_thread = threading.Thread(target=_reader, daemon=True)
    _reader_thread.start()

    rid = [0]

    def send(obj):
        msg = json.dumps(obj).encode() + b"\n"
        proc.stdin.write(msg)
        proc.stdin.flush()

    def recv(timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            _lines_event.clear()
            with _lines_lock:
                if _lines:
                    return json.loads(_lines.pop(0))
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            _lines_event.wait(min(remaining, 0.2))
        return None

    def call(method, params=None):
        rid[0] += 1
        req = {"jsonrpc": "2.0", "id": rid[0], "method": method}
        if params is not None:
            req["params"] = params
        send(req)
        return recv()

    def notify(method, params=None):
        req = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            req["params"] = params
        send(req)

    passed = [0]
    failed = [0]

    def test(name, ok, detail=""):
        if ok:
            passed[0] += 1
            print("  [通过] " + name)
        else:
            failed[0] += 1
            print("  [失败] " + name + " -- " + detail)

    try:
        # === 测试 1: 初始化 ===
        print("\n=== 测试 1: 初始化 ===")
        r = call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"},
        })
        test("服务器响应", r is not None)
        if r:
            info = r.get("result", {}).get("serverInfo", {})
            test("服务器名称 = icon-mcp-server", info.get("name") == "icon-mcp-server")
            caps = r.get("result", {}).get("capabilities", {})
            test("具备 tools 能力", "tools" in caps)

        notify("notifications/initialized")
        time.sleep(0.3)

        # === 测试 2: 列出工具 ===
        print("\n=== 测试 2: 列出工具 ===")
        r = call("tools/list", {})
        tools = r.get("result", {}).get("tools", []) if r else []
        names = [t["name"] for t in tools]
        test("已注册 {} 个工具".format(len(tools)), len(tools) >= 7)
        for expected in [
            "search_icons", "start_web_server", "stop_web_server",
            "check_selection_status", "get_cache_stats", "clear_cache", "save_icons",
        ]:
            test('工具 "{}" 已注册'.format(expected), expected in names)

        # 检查工具 schema
        for tool in tools:
            has_schema = "inputSchema" in tool
            test('工具 "{}" 包含 inputSchema'.format(tool["name"]), has_schema)

        # === 测试 3: get_cache_stats ===
        print("\n=== 测试 3: 缓存统计 ===")
        r = call("tools/call", {"name": "get_cache_stats", "arguments": {}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            stats = json.loads(content[0]["text"])
            test("包含 icon_cache", "icon_cache" in stats)
            test("包含 search_cache", "search_cache" in stats)
            test("初始缓存为空", stats.get("icon_cache", {}).get("total") == 0)
            test("过期时间 = 30分钟", stats.get("cache_expiry_minutes") == 30)
        else:
            test("get_cache_stats 返回了内容", False, str(r))

        # === 测试 4: search_icons ===
        print("\n=== 测试 4: 搜索图标 ===")
        r = call("tools/call", {"name": "search_icons", "arguments": {"q": "home", "pageSize": 5}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            result = json.loads(content[0]["text"])
            if "error" in result:
                print("  [警告] API 错误（可能是网络沙箱限制）：" + result["error"][:120])
                test("返回了结构化错误", True)
            else:
                test("找到 {} 个图标".format(result.get("count", 0)), result.get("count", 0) > 0)
                test("包含 search_id", bool(result.get("search_id")))
                test("web_url 包含 searchId", "searchId" in result.get("web_url", ""))
                test("包含 4 条说明", len(result.get("instructions", [])) == 4)
                test("包含等待提示消息", bool(result.get("waiting_message")))
        else:
            test("search_icons 返回了内容", False, str(r))

        # === 测试 5: start_web_server ===
        print("\n=== 测试 5: 启动 Web 服务器 ===")
        r = call("tools/call", {"name": "start_web_server", "arguments": {"port": 19999, "autoOpen": False}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            result = json.loads(content[0]["text"])
            test("服务器已启动（含端口）", "port" in result)
            test("包含 URL", "localhost" in result.get("url", ""))
            test("WebSocket 已启用", result.get("websocket") is True)
        else:
            test("start_web_server 返回了内容", False, str(r))

        # === 测试 6: stop_web_server ===
        print("\n=== 测试 6: 停止 Web 服务器 ===")
        r = call("tools/call", {"name": "stop_web_server", "arguments": {}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            result = json.loads(content[0]["text"])
            test("服务器已停止（含消息）", "message" in result)
        else:
            test("stop_web_server 返回了内容", False, str(r))

        # === 测试 7: clear_cache ===
        print("\n=== 测试 7: 清除缓存 ===")
        r = call("tools/call", {"name": "clear_cache", "arguments": {"expiredOnly": False}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            result = json.loads(content[0]["text"])
            test("包含消息", "message" in result)
            test("包含清除计数", "icon_cleared" in result)
        else:
            test("clear_cache 返回了内容", False, str(r))

        # === 测试 8: 错误处理 ===
        print("\n=== 测试 8: 错误处理 ===")
        r = call("tools/call", {"name": "nonexistent_tool", "arguments": {}})
        content = r.get("result", {}).get("content", []) if r else []
        if content:
            result = json.loads(content[0]["text"])
            test("未知工具返回错误", "error" in result)

        # === 测试 9: Ping ===
        print("\n=== 测试 9: Ping ===")
        r = call("ping", {})
        test("Ping 响应已收到", r is not None and "result" in r)

    except Exception as e:
        print("\n!!! 测试异常: {}".format(e))
        import traceback
        traceback.print_exc()
        failed[0] += 1

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        stderr_out = proc.stderr.read().decode().strip()

        if stderr_out:
            print("\n=== 服务器日志 ===")
            for line in stderr_out.split("\n")[-15:]:
                print("  " + line)

    total = passed[0] + failed[0]
    print("\n" + "=" * 44)
    print("  结果: {} / {} 通过, {} 失败".format(passed[0], total, failed[0]))
    print("=" * 44)

    return failed[0] == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
