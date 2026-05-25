"""CONCEPT:LGTM-002 Main FastMCP server and tool registration."""
import os
import sys
from typing import Any

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import create_mcp_server
from dotenv import find_dotenv, load_dotenv
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from lgtm_mcp.mcp.mcp_alertmanager import register_alertmanager_tools
from lgtm_mcp.mcp.mcp_grafana import register_grafana_tools

__version__ = "0.15.0"
logger = get_logger(name="lgtm_mcp")

def get_mcp_instance() -> tuple[Any, ...]:
    load_dotenv(find_dotenv())
    args, mcp, middlewares = create_mcp_server(
        name="LGTM MCP MCP",
        version=__version__,
        instructions="LGTM MCP MCP Server - Managed dynamic operations.",
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    DEFAULT_ALERTMANAGERTOOL = to_boolean(os.getenv("ALERTMANAGERTOOL", "True"))
    if DEFAULT_ALERTMANAGERTOOL:
        register_alertmanager_tools(mcp)

    DEFAULT_GRAFANATOOL = to_boolean(os.getenv("GRAFANATOOL", "True"))
    if DEFAULT_GRAFANATOOL:
        register_grafana_tools(mcp)

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares

def mcp_server() -> None:
    mcp, args, middlewares = get_mcp_instance()
    print(f"LGTM MCP MCP v{__version__}", file=sys.stderr)
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    mcp_server()