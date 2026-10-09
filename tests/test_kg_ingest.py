"""Native epistemic-graph typed-node ingestion — Wire-First coverage for lgtm-mcp.

Exercises the real ``ingest_entities`` / ``ingest_dashboards`` / ``ingest_alerts`` seam
against a fake transport boundary (one level below the SDK's own request builder),
asserting the Grafana dashboard -> :Dashboard / Alertmanager alert -> :Alert/:Receiver
mapping on the real generated ``SourceRecord``/``SourceRelationship`` shapes.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from lgtm_mcp.kg_ingest import ingest_alerts, ingest_dashboards, ingest_entities

_CONNECTOR = "lgtm-mcp"


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: Any) -> Any:
        raise AssertionError("this connector's ingestion carries no media")


@pytest.fixture
def ingest():
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


def _records_by_id(request: Any) -> dict[str, Any]:
    return {r.record_id: r for r in request.records}


def _mapping_reference(node_type: str) -> str:
    return f"manifest:{_CONNECTOR}#schema_mappings/{node_type}"


def _relation_reference(source_node_type: str, relationship: str) -> str:
    return f"manifest:{_CONNECTOR}#resources/{source_node_type}/relations/{relationship}"


@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "a", "node_type": "Alert", "name": "HighCPU"},
            {"id": "b", "node_type": "Receiver", "name": "pagerduty"},
        ],
        [{"source": "a", "target": "b", "relationship": "routedTo"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    records = _records_by_id(request)
    assert set(records) == {"a", "b"}
    assert records["a"].mapping_reference == _mapping_reference("Alert")
    assert records["a"].payload["name"] == "HighCPU"

    rel = request.relationships[0]
    assert rel.source.record_id == "a"
    assert rel.target.record_id == "b"
    assert rel.relation_reference == _relation_reference("Alert", "routedTo")


@pytest.mark.asyncio
async def test_ingest_dashboards_maps_dashboard_nodes(ingest):
    service, transport = ingest
    res = await ingest_dashboards(
        [
            {
                "uid": "abc123",
                "title": "Node Exporter",
                "url": "/d/abc123/node-exporter",
                "type": "dash-db",
                "tags": ["prod", "linux"],
                "folderTitle": "Infra",
            },
            {"uid": "fold1", "title": "Infra", "type": "dash-folder"},
        ],
        ingest=service,
    )
    # folder is skipped -> only the dashboard node
    assert res == {"nodes": 1, "edges": 0}
    request = transport.requests[0]
    node = _records_by_id(request)["observability:dashboard:abc123"]
    assert node.mapping_reference == _mapping_reference("Dashboard")
    assert node.payload["dashboardTitle"] == "Node Exporter"
    assert node.payload["tags"] == "prod,linux"
    assert node.payload["externalToolId"] == "abc123"


@pytest.mark.asyncio
async def test_ingest_alerts_maps_alert_and_receiver(ingest):
    service, transport = ingest
    res = await ingest_alerts(
        [
            {
                "fingerprint": "deadbeef",
                "labels": {"alertname": "HighCPU", "severity": "critical"},
                "status": {"state": "active"},
                "startsAt": "2026-07-04T00:00:00Z",
                "generatorURL": "http://prom/graph",
                "receivers": [{"name": "pagerduty"}],
            }
        ],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    records = _records_by_id(request)
    alert = records["observability:alert:deadbeef"]
    assert alert.mapping_reference == _mapping_reference("Alert")
    assert alert.payload["name"] == "HighCPU"
    assert alert.payload["severity"] == "critical"
    assert alert.payload["alertState"] == "active"
    assert (
        records["observability:receiver:pagerduty"].mapping_reference
        == _mapping_reference("Receiver")
    )
    rel = request.relationships[0]
    assert rel.source.record_id == "observability:alert:deadbeef"
    assert rel.target.record_id == "observability:receiver:pagerduty"
    assert rel.relation_reference == _relation_reference("Alert", "routedTo")


@pytest.mark.asyncio
async def test_retired_structural_alias_is_rejected(ingest):
    service, _ = ingest
    with pytest.raises(IngestError, match="needs an id and a node_type"):
        await ingest_entities([{"id": "a", "type": "Alert"}], ingest=service)


@pytest.mark.asyncio
async def test_empty_native_ingest_is_rejected(ingest):
    service, _ = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
