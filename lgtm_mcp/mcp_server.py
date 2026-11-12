"""Hand-written LGTM tools: the knowledge-graph ingest operations.

Every Alertmanager and Grafana operation is served by the SDK as one typed tool per
client method (``lgtm_get_alerts``, ``lgtm_create_silence``, ``lgtm_get_dashboards``,
...). Only the ingest tools, which are not client-method wrappers, are written here.
"""

import json
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from fastmcp.utilities.logging import get_logger
from pydantic import Field
from scion_sdk.mcp.concurrency import run_blocking

from lgtm_mcp.auth import get_client

logger = get_logger(name="lgtm_mcp")


def register_alertmanager_tools(mcp: FastMCP):
    """Register the Alertmanager ingest tool.
    CONCEPT:LG-OS.governance.lgtm-2
    """

    @mcp.tool(tags={"alertmanager", "kg"})
    async def lgtm_ingest_alerts(
        params_json: str = Field(
            default="{}",
            description="JSON string of get_alerts filters (e.g. active, silenced, filter).",
        ),
        client=Depends(get_client),
        ctx: Context | None = None,
    ) -> Any:
        """Natively ingest Alertmanager alerts into medulla as typed :Alert nodes.

        Lists alerts via the Alertmanager API and pushes them (with their :Receiver +
        :routedTo links) into the knowledge graph via the fast engine client.
        Best-effort: ``ingested`` is ``None`` when no engine is reachable.
        CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        from lgtm_mcp.kg_ingest import ingest_alerts

        kwargs = json.loads(params_json) if params_json else {}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        result = await run_blocking(client.get_alerts, **kwargs)
        records = result if isinstance(result, list) else []
        alerts = [r for r in records if isinstance(r, dict)]
        ingested = await ingest_alerts(alerts)
        return {"listed": len(alerts), "ingested": ingested}


def register_grafana_tools(mcp: FastMCP):
    """Register the Grafana ingest tool.
    CONCEPT:LG-OS.governance.lgtm-2
    """

    @mcp.tool(tags={"grafana", "kg"})
    async def lgtm_ingest_dashboards(
        params_json: str = Field(
            default="{}",
            description="Reserved for future get_dashboards filters (currently none).",
        ),
        client=Depends(get_client),
        ctx: Context | None = None,
    ) -> Any:
        """Natively ingest Grafana dashboards into medulla as typed :Dashboard nodes.

        Lists dashboards via the Grafana search API and pushes them into the knowledge
        graph via the fast engine client. Best-effort: ``ingested`` is ``None`` when no
        engine is reachable. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        from lgtm_mcp.kg_ingest import ingest_dashboards

        result = await run_blocking(client.get_dashboards)
        records = result if isinstance(result, list) else []
        dashboards = [r for r in records if isinstance(r, dict)]
        ingested = await ingest_dashboards(dashboards)
        return {"listed": len(dashboards), "ingested": ingested}
