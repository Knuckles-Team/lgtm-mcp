"""Native epistemic-graph typed-node ingestion — Wire-First coverage for lgtm-mcp.

Exercises the real ``ingest_entities`` / ``ingest_dashboards`` / ``ingest_alerts`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit + edge
calls and the Grafana dashboard → :Dashboard / Alertmanager alert → :Alert/:Receiver
mapping. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from lgtm_mcp.kg_ingest import ingest_alerts, ingest_dashboards, ingest_entities


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "type": "Alert", "name": "HighCPU"},
            {"id": "b", "type": "Receiver", "name": "pagerduty"},
        ],
        [{"source": "a", "target": "b", "type": "routedTo"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "b"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "lgtm-mcp"
    assert c.txn.nodes["a"]["domain"] == "observability"
    assert c.edges.edges == [("a", "b", {"type": "routedTo"})]


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
    assert node["type"] == "Dashboard"
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
    assert alert["type"] == "Alert"
    assert alert["name"] == "HighCPU"
    assert alert["severity"] == "critical"
    assert alert["alertState"] == "active"
    assert c.txn.nodes["observability:receiver:pagerduty"]["type"] == "Receiver"
    assert c.edges.edges == [
        (
            "observability:alert:deadbeef",
            "observability:receiver:pagerduty",
            {"type": "routedTo"},
        )
    ]


def test_ingest_noops_without_engine():
    # No injected client + no reachable engine -> clean no-op.
    assert (
        ingest_entities([{"id": "a", "type": "Alert"}], client=None, graph=None) is None
    )


def test_ingest_empty_is_noop():
    assert ingest_entities([], client=_FakeClient()) is None
    assert ingest_dashboards([], client=_FakeClient()) is None
    assert ingest_alerts([], client=_FakeClient()) is None
