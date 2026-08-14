"""Main FastMCP server and tool registration."""

import sys
from typing import Any

from agent_utilities.core.config import load_config
from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from agent_utilities.mcp.server_factory import create_mcp_server
from agent_utilities.mcp.verbose_tools import register_tool_surface
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from fastmcp.utilities.logging import get_logger
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from lgtm_mcp.api_client import Api
from lgtm_mcp.auth import get_client

__version__ = "0.15.0"
logger = get_logger(name="lgtm_mcp")


def _auto_ingest_dashboards(result: Any) -> None:
    """Best-effort native KG ingest of a get_dashboards result (no-op without engine)."""
    try:
        from lgtm_mcp.kg_ingest import ingest_dashboards

        records = result if isinstance(result, list) else []
        ingest_dashboards([r for r in records if isinstance(r, dict)])
    except Exception as e:  # noqa: BLE001 — ingestion is best-effort
        logger.debug("Operation failed: error_type=%s", type(e).__name__)


def _auto_ingest_alerts(result: Any) -> None:
    """Best-effort native KG ingest of a get_alerts result (no-op without engine)."""
    try:
        from lgtm_mcp.kg_ingest import ingest_alerts

        records = result if isinstance(result, list) else []
        ingest_alerts([r for r in records if isinstance(r, dict)])
    except Exception as e:  # noqa: BLE001 — ingestion is best-effort
        logger.debug("Operation failed: error_type=%s", type(e).__name__)


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
    CONCEPT:LG-OS.governance.lgtm-2
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
        except Exception:
            return {"error": "Operation failed"}

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
            result = await run_blocking(client.get_alerts, **kwargs)
            _auto_ingest_alerts(result)
            return result
        if action == "post_alerts":
            return await run_blocking(client.post_alerts, **kwargs)
        if action == "create_alerts":
            return await run_blocking(client.create_alerts, **kwargs)
        if action == "get_alert_groups":
            return await run_blocking(client.get_alert_groups, **kwargs)

        raise ValueError(f"Unknown Alertmanager action: {action}")

    @mcp.tool(tags={"alertmanager", "kg"})
    async def lgtm_ingest_alerts(
        params_json: str = Field(
            default="{}",
            description="JSON string of get_alerts filters (e.g. active, silenced, filter).",
        ),
        client=Depends(get_client),
        ctx: Context | None = None,
    ) -> Any:
        """Natively ingest Alertmanager alerts into epistemic-graph as typed :Alert nodes.

        Lists alerts via the Alertmanager API and pushes them (with their :Receiver +
        :routedTo links) into the knowledge graph via the fast engine client.
        Best-effort: ``ingested`` is ``None`` when no engine is reachable.
        CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        import json as _json

        from lgtm_mcp.kg_ingest import ingest_alerts

        kwargs = _json.loads(params_json) if params_json else {}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        result = await run_blocking(client.get_alerts, **kwargs)
        records = result if isinstance(result, list) else []
        alerts = [r for r in records if isinstance(r, dict)]
        ingested = ingest_alerts(alerts)
        return {"listed": len(alerts), "ingested": ingested}


GRAFANA_ACTIONS = (
    "get_dashboards",
    "create_dashboard",
    "query_datasource",
)


def register_grafana_tools(mcp: FastMCP):
    """Register LGTM MCP Grafana tools.
    CONCEPT:LG-OS.governance.lgtm-2
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
        except Exception:
            return {"error": "Operation failed"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, GRAFANA_ACTIONS, service="lgtm-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "get_dashboards":
            result = await run_blocking(client.get_dashboards, **kwargs)
            _auto_ingest_dashboards(result)
            return result
        if action == "create_dashboard":
            return await run_blocking(client.create_dashboard, **kwargs)
        if action == "query_datasource":
            return await run_blocking(client.query_datasource, **kwargs)

        raise ValueError(f"Unknown Grafana action: {action}")

    @mcp.tool(tags={"grafana", "kg"})
    async def lgtm_ingest_dashboards(
        params_json: str = Field(
            default="{}",
            description="Reserved for future get_dashboards filters (currently none).",
        ),
        client=Depends(get_client),
        ctx: Context | None = None,
    ) -> Any:
        """Natively ingest Grafana dashboards into epistemic-graph as typed :Dashboard nodes.

        Lists dashboards via the Grafana search API and pushes them into the knowledge
        graph via the fast engine client. Best-effort: ``ingested`` is ``None`` when no
        engine is reachable. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        from lgtm_mcp.kg_ingest import ingest_dashboards

        result = await run_blocking(client.get_dashboards)
        records = result if isinstance(result, list) else []
        dashboards = [r for r in records if isinstance(r, dict)]
        ingested = ingest_dashboards(dashboards)
        return {"listed": len(dashboards), "ingested": ingested}


def get_mcp_instance() -> tuple[Any, ...]:
    load_config()
    args, mcp, middlewares = create_mcp_server(
        name="LGTM MCP MCP",
        version=__version__,
        instructions="LGTM MCP MCP Server - Managed dynamic operations.",
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    registered_tags = register_tool_surface(
        mcp,
        client_cls=Api,
        get_client=get_client,
        service="lgtm-mcp",
        tools_module=sys.modules[__name__],
    )
    logger.info("Registered condensed tool surfaces: count=%d", len(registered_tags))

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
