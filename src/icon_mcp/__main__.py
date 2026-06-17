"""直接运行包: python -m icon_mcp"""

import argparse
import asyncio
import json
import os
import sys

from icon_mcp.config import ServerConfig
from icon_mcp.server import MCPIconServer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP 图标服务器 - 从 iconfont.cn 搜索和获取图标"
    )
    parser.add_argument("--port", type=int, default=None, help="Web server port")
    parser.add_argument("--auto-open", action="store_true", default=None, help="Auto-open browser")
    parser.add_argument("--auto-start-web", action="store_true", default=None, help="Auto-start web server")
    parser.add_argument("--language", choices=["en", "zh-CN"], default=None, help="界面语言")
    parser.add_argument("--test", type=str, default=None, help="测试模式：直接搜索指定关键词并输出结果，然后退出")

    args = parser.parse_args()

    config = ServerConfig()
    if args.port is not None:
        config.web_server_port = args.port
    if args.auto_open is not None:
        config.web_server_auto_open = args.auto_open
    if args.auto_start_web is not None:
        config.auto_start_web_server = args.auto_start_web
    if args.language is not None:
        config.language = args.language
        os.environ["LANGUAGE"] = args.language

    server = MCPIconServer(config)

    # 测试模式
    if args.test is not None:
        try:
            result = asyncio.run(server.test_search(args.test))
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"测试失败: {e}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        asyncio.run(server.run())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"致命错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
