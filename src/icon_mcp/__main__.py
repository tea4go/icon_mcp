"""Allow running the package directly: python -m icon_mcp"""

from icon_mcp.config import ServerConfig
from icon_mcp.server import MCPIconServer
import asyncio
import sys


def main() -> None:
    config = ServerConfig()
    server = MCPIconServer(config)
    try:
        asyncio.run(server.run())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
