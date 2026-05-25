"""MCP tools for grafana operations."""

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from lgtm_mcp.auth import get_client


def register_grafana_tools(mcp: FastMCP):
    """Register LGTM MCP grafana tools.
    CONCEPT:LGTM-001
    """

    @mcp.tool(tags={"grafana"})
    async def lgtm_mcp_grafana(
        action: str = Field(
            description="Action to perform. Must be one of: 'get_dashboards', 'create_dashboard', 'query_datasource'"
        ),
        params_json: str = Field(
            default="{}", description="JSON string of parameters."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Manage LGTM MCP grafana operations."""
        if ctx:
            await ctx.info("Executing grafana operations...")
        import json

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        if action == "get_dashboards":
            return client.get_dashboards(**kwargs)
        if action == "create_dashboard":
            return client.create_dashboard(**kwargs)
        if action == "query_datasource":
            return client.query_datasource(**kwargs)

        raise ValueError(f"Unknown action: {action}")
