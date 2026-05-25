"""MCP tools for alertmanager operations."""
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field
from lgtm_mcp.auth import get_client

def register_alertmanager_tools(mcp: FastMCP):
    """Register LGTM MCP alertmanager tools.
    CONCEPT:LGTM-001
    """
    @mcp.tool(tags={"alertmanager"})
    async def lgtm_mcp_alertmanager(
        action: str = Field(description="Action to perform. Must be one of: 'get_alerts', 'create_silence', 'delete_silence', 'get_status'"),
        params_json: str = Field(default="{}", description="JSON string of parameters."),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Manage LGTM MCP alertmanager operations."""
        if ctx:
            await ctx.info("Executing alertmanager operations...")
        import json
        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        if action == "get_alerts":
            return client.get_alerts(**kwargs)
        if action == "create_silence":
            return client.create_silence(**kwargs)
        if action == "delete_silence":
            return client.delete_silence(**kwargs)
        if action == "get_status":
            return client.get_status(**kwargs)

        raise ValueError(f"Unknown action: {action}")
