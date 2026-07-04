---
name: lgtm-grafana-dashboards
description: >-
  Grafana dashboard and datasource operations over the lgtm-mcp MCP server — search
  existing dashboards, create a dashboard from a JSON model, and run ad-hoc queries
  against a Grafana datasource (Prometheus/Loki/etc.). Use when the agent must
  discover what dashboards exist, provision a new dashboard, or pull metric/log data
  through Grafana's datasource proxy. Do NOT use for Alertmanager alert/silence
  lifecycle (use lgtm-alertmanager-alerts) or for raw Prometheus HTTP outside
  Grafana.
license: MIT
tags: [lgtm, grafana, dashboards, observability, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# LGTM Grafana Dashboards

Domain-typed access to the **Grafana** surface of the LGTM stack via the `lgtm-mcp`
MCP server: dashboard search/create and datasource queries. Reads are natively
mirrored into the knowledge graph as `:Dashboard` nodes.

## When to use
- List / search existing Grafana dashboards (folders, titles, uids, tags).
- Create a new dashboard from a dashboard JSON model.
- Query a Grafana datasource by id (SQL/PromQL-style raw query via the tsdb proxy).

## When NOT to use
- Alert firing state, silences, receivers, or Alertmanager status → `lgtm-alertmanager-alerts`.
- Talking to Prometheus/Loki directly outside Grafana's proxy → use the native
  KG `kg-promql` / metrics tooling instead.
- Generic HTTP or non-observability APIs.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`lgtm-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `GRAFANA_URL` | ✅ | Grafana base URL (falls back to `LGTM_MCP_BASE_URL`) |
| `LGTM_TOKEN` | one of | Grafana API token (Bearer) |
| `LGTM_MCP_USERNAME` / `LGTM_MCP_PASSWORD` | one of | Basic-auth instead of a token |
| `LGTM_MCP_SSL_VERIFY` | optional | TLS verification toggle |

`MCP_TOOL_MODE` (`condensed`|`verbose`|`both`) selects the condensed surface (used
below) vs. the one-to-one verbose tools.

## Tools & actions
Prefer the **condensed** tool; it takes `action` + a `params_json` **JSON string**
whose keys are passed straight to the client method.

| Condensed tool | Actions |
|----------------|---------|
| `lgtm_mcp_grafana` | `get_dashboards`, `create_dashboard`, `query_datasource` |
| `lgtm_ingest_dashboards` | (KG) list dashboards + push `:Dashboard` nodes |

### Key parameters
- `get_dashboards` — no parameters; returns the `/api/search` result list.
- `create_dashboard` — `dashboard_data`: the full dashboards-db payload
  (`{"dashboard": {...}, "folderId": N, "overwrite": bool}`).
- `query_datasource` — `datasource_id` (int) + `query` (raw string).

## Recipes (`params_json`)
List all dashboards:
```json
{}
```
Create a dashboard (minimal):
```json
{"dashboard_data":{"dashboard":{"title":"Node Health","panels":[]},"overwrite":false}}
```
Query a datasource:
```json
{"datasource_id":1,"query":"SELECT 1"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- `get_dashboards` returns `dash-folder` rows alongside `dash-db` rows; the KG
  ingestion skips folders and only maps real dashboards.
- `query_datasource` posts to the legacy `/api/tsdb/query` proxy with
  `format: "table"`; use datasource-native syntax (PromQL for Prometheus,
  LogQL for Loki) as the `query`.
- Dashboard `uid` is the stable id — the KG node id is `observability:dashboard:<uid>`.

## Related
- `lgtm-alertmanager-alerts` — the Alertmanager half of this package.
- `lgtm_ingest_dashboards` pushes dashboards into the KG; `get_dashboards` also
  auto-ingests on every read (best-effort, no-op without a reachable engine).
