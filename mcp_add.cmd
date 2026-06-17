@echo off
claude mcp remove -s user icon-mcp
claude mcp add -s user icon-mcp -- uv --directory "c:\MyWork\AiCode\icon_mcp" run python run.py --port 31245 --language zh-CN --auto-start-web