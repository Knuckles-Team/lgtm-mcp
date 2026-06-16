"""Main FastMCP server and tool registration."""

import os
import sys
from typing import Any

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import (
    create_mcp_server,
    resolve_action,
    run_blocking,
)
from dotenv import find_dotenv, load_dotenv
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from fastmcp.utilities.logging import get_logger
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from lgtm_mcp.auth import get_client

__version__ = "0.15.0"
logger = get_logger(name="lgtm_mcp")


ALERTMANAGER_ACTIONS = (
    "get_status",
    "get_receivers",
    "get_silences",
    "post_silences",
    "create_silence",
    "get_silence",
    "delete_silence",
    "get_alerts",
    "post_alerts",
    "create_alerts",
    "get_alert_groups",
)


def register_alertmanager_tools(mcp: FastMCP):
    """Register LGTM MCP Alertmanager tools.
    CONCEPT:LGTM-002
    """

    @mcp.tool(tags={"alertmanager"})
    async def lgtm_mcp_alertmanager(
        action: str = Field(
            description=(
                "Action to perform. Must be one of: "
                "'get_status', 'get_receivers', 'get_silences', 'post_silences', "
                "'create_silence', 'get_silence', 'delete_silence', 'get_alerts', "
                "'post_alerts', 'create_alerts', 'get_alert_groups'"
            )
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters matching the method signature.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Manage LGTM MCP Alertmanager operations."""
        if ctx:
            await ctx.info(f"Executing Alertmanager operation '{action}'...")
        import json

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ALERTMANAGER_ACTIONS, service="lgtm-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "get_status":
            return await run_blocking(client.get_status, **kwargs)
        if action == "get_receivers":
            return await run_blocking(client.get_receivers, **kwargs)
        if action == "get_silences":
            return await run_blocking(client.get_silences, **kwargs)
        if action == "post_silences":
            return await run_blocking(client.post_silences, **kwargs)
        if action == "create_silence":
            return await run_blocking(client.create_silence, **kwargs)
        if action == "get_silence":
            return await run_blocking(client.get_silence, **kwargs)
        if action == "delete_silence":
            return await run_blocking(client.delete_silence, **kwargs)
        if action == "get_alerts":
            return await run_blocking(client.get_alerts, **kwargs)
        if action == "post_alerts":
            return await run_blocking(client.post_alerts, **kwargs)
        if action == "create_alerts":
            return await run_blocking(client.create_alerts, **kwargs)
        if action == "get_alert_groups":
            return await run_blocking(client.get_alert_groups, **kwargs)

        raise ValueError(f"Unknown Alertmanager action: {action}")


GRAFANA_ACTIONS = (
    "get_dashboards",
    "create_dashboard",
    "query_datasource",
)


def register_grafana_tools(mcp: FastMCP):
    """Register LGTM MCP Grafana tools.
    CONCEPT:LGTM-002
    """

    @mcp.tool(tags={"grafana"})
    async def lgtm_mcp_grafana(
        action: str = Field(
            description=(
                "Action to perform. Must be one of: "
                "'get_dashboards', 'create_dashboard', 'query_datasource'"
            )
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters matching the method signature.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Manage LGTM MCP Grafana operations."""
        if ctx:
            await ctx.info(f"Executing Grafana operation '{action}'...")
        import json

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, GRAFANA_ACTIONS, service="lgtm-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "get_dashboards":
            return await run_blocking(client.get_dashboards, **kwargs)
        if action == "create_dashboard":
            return await run_blocking(client.create_dashboard, **kwargs)
        if action == "query_datasource":
            return await run_blocking(client.query_datasource, **kwargs)

        raise ValueError(f"Unknown Grafana action: {action}")


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
