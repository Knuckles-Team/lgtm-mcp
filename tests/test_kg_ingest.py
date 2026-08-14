"""Native epistemic-graph typed-node ingestion — Wire-First coverage for lgtm-mcp.

Exercises the real ``ingest_entities`` / ``ingest_dashboards`` / ``ingest_alerts`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit + edge
calls and the Grafana dashboard → :Dashboard / Alertmanager alert → :Alert/:Receiver
mapping. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.brain_context import ActorContext, use_actor
from agent_utilities.models.company_brain import ActorType
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session

from lgtm_mcp.kg_ingest import ingest_alerts, ingest_dashboards, ingest_entities


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Alert", "name": "HighCPU"},
            {"id": "b", "node_type": "Receiver", "name": "pagerduty"},
        ],
        [{"source": "a", "target": "b", "relationship": "routedTo"}],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    assert set(c.nodes.values) == {"a", "b"}
    # provenance is stamped
    assert c.nodes.values["a"]["source"] == "lgtm-mcp"
    assert c.nodes.values["a"]["domain"] == "observability"
    assert c.changes.edges == [("a", "b", {"relationship": "routedTo"})]


def test_ingest_dashboards_maps_dashboard_nodes():
    c = _FakeClient()
    res = ingest_dashboards(
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
        client=c,
    )
    # folder is skipped -> only the dashboard node
    assert res == {"nodes": 1, "edges": 0}
    node = c.nodes.values["observability:dashboard:abc123"]
    assert node["node_type"] == "Dashboard"
    assert node["dashboardTitle"] == "Node Exporter"
    assert node["tags"] == "prod,linux"
    assert node["externalToolId"] == "abc123"


def test_ingest_alerts_maps_alert_and_receiver():
    c = _FakeClient()
    res = ingest_alerts(
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
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    alert = c.nodes.values["observability:alert:deadbeef"]
    assert alert["node_type"] == "Alert"
    assert alert["name"] == "HighCPU"
    assert alert["severity"] == "critical"
    assert alert["alertState"] == "active"
    assert c.nodes.values["observability:receiver:pagerduty"]["node_type"] == "Receiver"
    assert c.changes.edges == [
        (
            "observability:alert:deadbeef",
            "observability:receiver:pagerduty",
            {"relationship": "routedTo"},
        )
    ]


def test_retired_structural_alias_is_rejected():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "a", "type": "Alert"}], client=_FakeClient())


def test_empty_native_ingest_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
