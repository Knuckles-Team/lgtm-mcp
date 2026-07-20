"""Native epistemic-graph typed-node ingestion — Wire-First coverage for lgtm-mcp.

Exercises the real ``ingest_entities`` / ``ingest_dashboards`` / ``ingest_alerts`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit + edge
calls and the Grafana dashboard → :Dashboard / Alertmanager alert → :Alert/:Receiver
mapping. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from lgtm_mcp.kg_ingest import ingest_alerts, ingest_dashboards, ingest_entities


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def add_edge(self, txn, source, target, props):
        self.edges.append((source, target, props))

    def commit(self, txn):
        self.committed = True
        return True


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Alert", "name": "HighCPU"},
            {"id": "b", "node_type": "Receiver", "name": "pagerduty"},
        ],
        [{"source": "a", "target": "b", "relationship": "routedTo"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "b"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "lgtm-mcp"
    assert c.txn.nodes["a"]["domain"] == "observability"
    assert c.txn.edges == [("a", "b", {"relationship": "routedTo"})]


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
        graph="__commons__",
    )
    # folder is skipped -> only the dashboard node
    assert res == {"nodes": 1, "edges": 0}
    node = c.txn.nodes["observability:dashboard:abc123"]
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
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    alert = c.txn.nodes["observability:alert:deadbeef"]
    assert alert["node_type"] == "Alert"
    assert alert["name"] == "HighCPU"
    assert alert["severity"] == "critical"
    assert alert["alertState"] == "active"
    assert c.txn.nodes["observability:receiver:pagerduty"]["node_type"] == "Receiver"
    assert c.txn.edges == [
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
