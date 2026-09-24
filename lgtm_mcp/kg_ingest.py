"""Native epistemic-graph ingestion for LGTM observability records.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("lgtm_mcp.kg")

_SOURCE = "lgtm-mcp"
_DOMAIN = "observability"


def ingest_entities(*args: object, **kwargs: object) -> object:
    """Write canonical typed nodes and relationships in one native transaction.

    SDK-GAP: Always raises now; see KnowledgeGraphIngestUnavailable.
    """
    _kg_unavailable("ingest_entities")


def ingest_documents(*args: object, **kwargs: object) -> object:
    """Write text records as canonical Document nodes.

    SDK-GAP: Always raises now; see KnowledgeGraphIngestUnavailable.
    """
    _kg_unavailable("ingest_documents")


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


def _map_alert(alert: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Map one Alertmanager alert to its ``:Alert`` node; None if it has no fingerprint id."""
    fp = alert.get("fingerprint")
    if not fp:
        return None
    labels = alert.get("labels") or {}
    status = alert.get("status") or {}
    aid = f"observability:alert:{fp}"
    entity = {
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
    return aid, entity


def _map_alert_receivers(
    aid: str, alert: dict[str, Any], seen_receivers: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map one alert's receivers to ``:Receiver`` nodes (deduped via seen_receivers,
    mutated in place) + ``routedTo`` edges from the alert."""
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for rcv in alert.get("receivers") or []:
        name = rcv.get("name") if isinstance(rcv, dict) else rcv
        if not name:
            continue
        rid = f"observability:receiver:{name}"
        if name not in seen_receivers:
            seen_receivers.add(name)
            entities.append({"id": rid, "node_type": "Receiver", "name": name})
        relationships.append({"source": aid, "target": rid, "relationship": "routedTo"})
    return entities, relationships


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
        mapped = _map_alert(alert)
        if mapped is None:
            continue
        aid, entity = mapped
        entities.append(entity)

        rcv_entities, rcv_relationships = _map_alert_receivers(
            aid, alert, seen_receivers
        )
        entities.extend(rcv_entities)
        relationships.extend(rcv_relationships)

    return ingest_entities(entities, relationships, client=client, graph=graph)


class KnowledgeGraphIngestUnavailable(RuntimeError):
    """Direct-to-graph ingestion is unavailable from this connector.

    SDK-GAP (EH-48x, /var/tmp/l9/finish/au-decon-G4c/SDK-GAPS.md): raised in
    place of the old ``agent_utilities.knowledge_graph`` native-ingest call --
    agent-connector-sdk has no facade over EG's typed ingestion protocol yet,
    and the fleet precedent (agents/world-reference-mcp) moves direct-to-graph
    delivery to agent_connector_sdk.runner/sinks at the deployment layer, out
    of connector scope.
    """


def _kg_unavailable(name: str) -> None:
    raise KnowledgeGraphIngestUnavailable(
        f"{name}: direct-to-graph ingestion moved out of connector code "
        "(agent-utilities removed); no agent-connector-sdk facade exists yet "
        "-- see SDK-GAPS.md"
    )
