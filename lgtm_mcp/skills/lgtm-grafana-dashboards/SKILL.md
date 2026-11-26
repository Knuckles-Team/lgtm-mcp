---
name: lgtm-grafana-dashboards
skill_type: skill
description: >-
  Grafana dashboard and datasource operations over the lgtm-mcp MCP server — search existing dashboards, create a dashboard from a JSON model, and run ad-hoc queries against a Grafana datasource (Prometheus/Loki/etc.). Use when the agent must discover what dashboards exist, provision a new dashboard, or pull metric/log data through Grafana's datasource proxy.
license: MIT
tags: [lgtm, grafana, dashboards, observability, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# LGTM Grafana Dashboards

Scope: Grafana dashboard and datasource operations over the lgtm-mcp MCP server — search existing dashboards, create a dashboard from a JSON model, and run ad-hoc queries against a Grafana datasource (Prometheus/Loki/etc.). Use when the agent must discover what dashboards exist, provision a new dashboard, or pull metric/log data through Grafana's datasource proxy. Do NOT use for Alertmanager alert/silence lifecycle (use lgtm-alertmanager-alerts) or for raw Prometheus HTTP outside Grafana.

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


## Steps

1. List dashboards with `lgtm_get_dashboards`, and verify the response contains `dash-db` rows with `uid` values.
2. Query a data source with `lgtm_query_datasource`(`datasource_id`, `query`) in its native syntax, and verify the response carries result rows.
3. Create a dashboard with `lgtm_create_dashboard`(`dashboard_data`) holding a `dashboard` object and `overwrite`, and verify the response returns a `uid`.
4. Confirm creation by calling `lgtm_get_dashboards` again, and verify the new `uid` and title are listed.
5. Persist state to the graph only when asked: call `lgtm_ingest_dashboards`, and verify the response reports ingested dashboards.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Authentication or connection error | `GRAFANA_URL` or credentials (`LGTM_TOKEN`, or `LGTM_MCP_USERNAME` with `LGTM_MCP_PASSWORD`) missing | Set `GRAFANA_URL` and one credential form, then call `lgtm_get_dashboards` again |
| Create fails because the dashboard exists | `overwrite` is false for an existing title or `uid` | Set `overwrite` to true only after the user approves replacing it |
| Query returns an error | Query not in the datasource's native syntax or wrong `datasource_id` | Use PromQL for Prometheus or LogQL for Loki and take the id from the data source list |

## Tools
One typed tool per operation; pass each argument by name.

| Tool | Use |
|------|-----|
| `lgtm_get_dashboards` | List dashboards (the search result) |
| `lgtm_create_dashboard` | Create or overwrite a dashboard |
| `lgtm_query_datasource` | Run a raw query against a data source |
| `lgtm_ingest_dashboards` | List dashboards and push `:Dashboard` nodes into the knowledge graph |

## Recipes (tool arguments)
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
