from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

# Skip if optional dependency is not installed
pytest.importorskip("aiohttp")
from aiohttp import web

from orchestrator.tools.mcp_adapter import register_mcp_http_adapter

server_path = Path("samples/integrations/mcp-client/mcp_client_server.py")
if not server_path.exists():
    pytest.skip("MCP client sample server not found; skipping adapter test", allow_module_level=True)
spec = spec_from_file_location("mcp_server", server_path)
if spec and spec.loader:
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    create_app = module.create_app
else:
    pytest.skip("Failed to load mcp_server module", allow_module_level=True)


@pytest.mark.asyncio
async def test_mcp_http_adapter_discover_and_execute() -> None:
    # Start mock server on localhost (not 127.0.0.1) to ensure binding works
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 0)
    await site.start()

    # Figure out bound port from socket
    server = site._server
    if server is None:
        raise RuntimeError("server not available")
    sockets = getattr(server, 'sockets', None)
    if not sockets:
        raise RuntimeError("server sockets not available")
    sock = sockets[0]
    addr = sock.getsockname()
    port = addr[1]
    base_url = f"http://localhost:{port}"
    plugin = register_mcp_http_adapter("external_mcp_http", base_url)

    # Discover tools
    tools = await plugin.discover()
    assert "process_user" in tools
    td = tools["process_user"]
    assert td.type == "mcp"
    assert td.input_schema and td.input_schema["type"] == "object"

    # Execute
    result = await plugin.execute("process_user", {"user": {"id": "u1", "profile": {"age": 42}}})
    assert isinstance(result, dict)
    assert result.get("ok") is True
    assert result.get("echo", {}).get("user", {}).get("profile", {}).get("age") == 42

    # Cleanup
    await runner.cleanup()
