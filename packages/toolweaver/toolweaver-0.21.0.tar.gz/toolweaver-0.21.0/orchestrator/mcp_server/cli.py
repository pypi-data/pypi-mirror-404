import argparse
import asyncio
import logging
import os
import sys

# Ensure cwd is in path to find orchestrator
sys.path.append(os.getcwd())

def main() -> None:
    parser = argparse.ArgumentParser(description="ToolWeaver MCP Integration")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start server command
    start_parser = subparsers.add_parser("start-server", help="Start MCP server over stdio")
    start_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.command == "start-server":
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        from orchestrator.mcp_server.server import serve
        try:
            asyncio.run(serve())
        except KeyboardInterrupt:
            # Stdio server is often stopped by closing stdin, which implies clean exit
            pass
        except Exception as e:
            logging.error(f"Server failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
