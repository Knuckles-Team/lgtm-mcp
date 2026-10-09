"""Native epistemic-graph ingestion for LGTM observability records.

All writes use ``agent_connector_sdk.ingest``'s generated SourceIngest client,
not a local ingestion helper. Nodes use canonical ``node_type`` and edges use
canonical ``relationship``.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_connector_sdk.ingest import (
    ChangeSet,
    Document,
    Entity,
    IngestBinding,
    IngestError,
    KnowledgeIngest,
    Relationship,
    current_ingest,
)

logger = logging.getLogger("lgtm_mcp.kg")

_BINDING = IngestBinding(connector="lgtm-mcp", stream="observability")

_ENTITY_RESERVED_KEYS = frozenset({"id", "node_type"})
_RELATIONSHIP_RESERVED_KEYS = frozenset({"source", "target", "relationship"})


def _to_entity(record: dict[str, Any]) -> Entity:
    return Entity(
        id=record.get("id"),
        node_type=record.get("node_type"),
        properties={
            key: value
            for key, value in record.items()
            if key not in _ENTITY_RESERVED_KEYS
        },
    )


def _to_relationship(record: dict[str, Any]) -> Relationship:
    properties = {
        key: value
        for key, value in record.items()
        if key not in _RELATIONSHIP_RESERVED_KEYS
    }
    return Relationship(
        source=record["source"],
        target=record["target"],
        relationship=record["relationship"],
        properties=properties or None,
    )


async def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships through the SDK ingest facade."""
    if not entities:
        raise IngestError("ingest_entities needs at least one entity")
    change_set = ChangeSet(
        entities=tuple(_to_entity(entity) for entity in entities),
        relationships=tuple(
            _to_relationship(relationship) for relationship in relationships or ()
        ),
    )
    service = ingest or current_ingest()
    receipt = await service.submit(_BINDING, change_set)
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


async def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Write text records as canonical Document nodes."""
    if not docs:
        raise IngestError("ingest_documents needs at least one document")
    change_set = ChangeSet(
        documents=tuple(
            Document(
                id=doc["id"],
                text=doc["text"],
                title=doc.get("title"),
                source_uri=doc.get("source_uri"),
                properties={
                    key: value
                    for key, value in doc.items()
                    if key not in {"id", "text", "title", "source_uri"}
                },
            )
            for doc in docs
        )
    )
    service = ingest or current_ingest()
    receipt = await service.submit(_BINDING, change_set)
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


def _dashboard_id(record: dict[str, Any]) -> str | None:
    ext = record.get("uid") or record.get("id")
    return str(ext) if ext is not None else None


async def ingest_dashboards(
    dashboards: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
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
    return await ingest_entities(entities, None, ingest=ingest)


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
        relationships.append(
            {"source": aid, "target": rid, "relationship": "routedTo"}
        )
    return entities, relationships


async def ingest_alerts(
    alerts: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
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

    return await ingest_entities(entities, relationships, ingest=ingest)
