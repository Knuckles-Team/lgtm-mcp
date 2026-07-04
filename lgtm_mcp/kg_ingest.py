"""Native epistemic-graph ingestion for LGTM / Alertmanager observability records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The lgtm-mcp connector natively
pushes its observability data into the ONE epistemic-graph knowledge graph as **typed
OWL nodes** — Grafana dashboards → ``:Dashboard`` and Alertmanager alert state →
``:Alert`` / ``:AlertGroup`` / ``:Silence`` / ``:Receiver`` (+ links) — matching the
classes federated by ``lgtm_mcp.ontology`` (``grafana.ttl`` + ``observability.ttl``).

The write path prefers the shared fleet primitive
``agent_utilities.knowledge_graph.memory.native_ingest``; when that is not present in
the installed ``agent_utilities`` it falls back to a self-contained txn over the
lightweight engine client (``GraphComputeEngine()._client`` + ``txn``) — the same fast
client the blob ``MediaStore`` uses, NOT the heavy in-process ingestion engine.

Everything is dependency-/engine-guarded: with no KG stack or no reachable engine every
entry point **no-ops** (returns ``None``), so the connector runs with zero KG
infrastructure. Node ids follow ``observability:<class>:<externalId>``.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("lgtm_mcp.kg")

_SOURCE = "lgtm-mcp"
_DOMAIN = "observability"
_DEFAULT_GRAPH = "__commons__"

# Prefer the shared fleet primitive; fall back to the local txn path when the
# installed agent_utilities does not yet ship it.
try:  # pragma: no cover - import shape depends on installed agent_utilities
    from agent_utilities.knowledge_graph.memory.native_ingest import (
        ingest_documents as _shared_ingest_documents,
    )
    from agent_utilities.knowledge_graph.memory.native_ingest import (
        ingest_entities as _shared_ingest_entities,
    )
except Exception:  # noqa: BLE001 — primitive not present -> use local fallback
    _shared_ingest_entities = None
    _shared_ingest_documents = None


def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or _DEFAULT_GRAPH)
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def _write_nodes(
    client: Any,
    graph: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
    *,
    source: str,
    domain: str,
) -> dict[str, int] | None:
    """Stamp provenance, MERGE the nodes in one txn, then add the edges."""
    nodes = [n for n in nodes if n.get("id")]
    if not nodes:
        return None
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", source)
            props.setdefault("domain", domain)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest[%s]: wrote %d nodes, %d edges", domain, len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed OWL nodes (+ edges) into epistemic-graph.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":<link>}]``.
    Returns ``{"nodes":n, "edges":m}`` or ``None`` (no engine / failure; never raises).
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None
    # When no client is injected, prefer the shared fleet primitive if available.
    if client is None and _shared_ingest_entities is not None:
        return _shared_ingest_entities(
            entities, relationships, source=source, domain=domain
        )
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _write_nodes(
        client,
        graph or _DEFAULT_GRAPH,
        entities,
        relationships,
        source=source,
        domain=domain,
    )


def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write text records as ``:Document`` nodes (semantic-search fodder)."""
    docs = [
        d for d in (docs or []) if d.get("id") and (d.get("text") or d.get("content"))
    ]
    if not docs:
        return None
    if client is None and _shared_ingest_documents is not None:
        return _shared_ingest_documents(docs, source=source, domain=domain)
    nodes: list[dict[str, Any]] = []
    for doc in docs:
        text = doc.get("text") or doc.get("content")
        node = {k: v for k, v in doc.items() if k != "content" and v is not None}
        node["type"] = "Document"
        node["text"] = text
        nodes.append(node)
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _write_nodes(
        client, graph or _DEFAULT_GRAPH, nodes, None, source=source, domain=domain
    )


def _dashboard_id(record: dict[str, Any]) -> str | None:
    ext = record.get("uid") or record.get("id")
    return str(ext) if ext is not None else None


def ingest_dashboards(
    dashboards: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
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
                "type": "Dashboard",
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
) -> dict[str, int] | None:
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
                "type": "Alert",
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
                entities.append({"id": rid, "type": "Receiver", "name": name})
            relationships.append({"source": aid, "target": rid, "type": "routedTo"})
    return ingest_entities(entities, relationships, client=client, graph=graph)
