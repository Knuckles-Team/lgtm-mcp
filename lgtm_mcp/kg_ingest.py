"""Native epistemic-graph ingestion for LGTM observability records.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_documents as _native_ingest_documents,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

logger = logging.getLogger("lgtm_mcp.kg")

_SOURCE = "lgtm-mcp"
_DOMAIN = "observability"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships in one native transaction."""
    return _native_ingest_entities(
        entities, relationships, source=source, domain=domain, client=client, graph=graph
    )


def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write text records as canonical Document nodes."""
    return _native_ingest_documents(
        docs, source=source, domain=domain, client=client, graph=graph
    )


def _dashboard_id(record: dict[str, Any]) -> str | None:
    ext = record.get("uid") or record.get("id")
    return str(ext) if ext is not None else None


def ingest_dashboards(
    dashboards: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map Grafana search results (``/api/search``) → ``:Dashboard`` nodes and ingest."""
    entities: list[dict[str, Any]] = []
    for dash in dashboards or []:
        did = _dashboard_id(dash)
        if did is None or dash.get("type") == "dash-folder":
            continue
        tags = dash.get("tags")
        entities.append(
            {
                "id": f"observability:dashboard:{did}",
                "node_type": "Dashboard",
                "dashboardTitle": dash.get("title"),
                "url": dash.get("url") or dash.get("uri"),
                "folderTitle": dash.get("folderTitle"),
                "tags": ",".join(tags) if isinstance(tags, list) else tags,
                "externalToolId": did,
            }
        )
    return ingest_entities(entities, None, client=client, graph=graph)


def ingest_alerts(
    alerts: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map Alertmanager alerts (``/api/v2/alerts``) → ``:Alert`` (+ ``:Receiver``) nodes.

    Each alert carries a ``fingerprint`` id, its ``labels`` (``alertname``/``severity``),
    ``status.state`` and firing window. Receivers become ``:Receiver`` nodes linked by a
    ``routedTo`` edge.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    seen_receivers: set[str] = set()
    for alert in alerts or []:
        fp = alert.get("fingerprint")
        if not fp:
            continue
        labels = alert.get("labels") or {}
        status = alert.get("status") or {}
        aid = f"observability:alert:{fp}"
        entities.append(
            {
                "id": aid,
                "node_type": "Alert",
                "name": labels.get("alertname"),
                "severity": labels.get("severity"),
                "alertState": status.get("state"),
                "startsAt": alert.get("startsAt"),
                "endsAt": alert.get("endsAt"),
                "url": alert.get("generatorURL"),
                "externalToolId": str(fp),
            }
        )
        for rcv in alert.get("receivers") or []:
            name = rcv.get("name") if isinstance(rcv, dict) else rcv
            if not name:
                continue
            rid = f"observability:receiver:{name}"
            if name not in seen_receivers:
                seen_receivers.add(name)
                entities.append({"id": rid, "node_type": "Receiver", "name": name})
            relationships.append({"source": aid, "target": rid, "relationship": "routedTo"})
    return ingest_entities(entities, relationships, client=client, graph=graph)
