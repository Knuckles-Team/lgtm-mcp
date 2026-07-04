---
name: lgtm-alertmanager-alerts
description: >-
  Alertmanager alert and silence operations over the lgtm-mcp MCP server — list
  active/silenced alerts and alert groups, read cluster status and receivers, and
  create/read/delete silences to mute noisy alerts. Use when the agent must triage
  firing alerts, understand routing/receivers, or silence an alert during
  maintenance. Do NOT use for Grafana dashboards or datasource queries (use
  lgtm-grafana-dashboards).
license: MIT
tags: [lgtm, alertmanager, alerts, silences, observability, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# LGTM Alertmanager Alerts

Domain-typed access to **Alertmanager** (v2 API) via the `lgtm-mcp` MCP server:
alert triage, alert-group inspection, receiver/status reads, and the silence
lifecycle. Reads are natively mirrored into the knowledge graph as `:Alert` (+
`:Receiver`) nodes.

## When to use
- List active / silenced / inhibited alerts, optionally filtered by label matcher.
- Read grouped alerts (`get_alert_groups`) and the receivers they route to.
- Check cluster/config `get_status` and configured `get_receivers`.
- Create, read, or delete a **silence** to mute alerts during maintenance.

## When NOT to use
- Grafana dashboards, panels, or datasource queries → `lgtm-grafana-dashboards`.
- Authoring alert *rules* (that lives in Grafana/Prometheus config, not Alertmanager).
- Long-term metric history — Alertmanager only knows currently-firing state.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`lgtm-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ALERTMANAGER_URL` | ✅ | Alertmanager base URL (falls back to `LGTM_MCP_BASE_URL`) |
| `LGTM_TOKEN` | one of | Bearer token |
| `LGTM_MCP_USERNAME` / `LGTM_MCP_PASSWORD` | one of | Basic-auth instead of a token |
| `LGTM_MCP_SSL_VERIFY` | optional | TLS verification toggle |

`MCP_TOOL_MODE` (`condensed`|`verbose`|`both`) selects the condensed surface (used
below) vs. the one-to-one verbose tools.

## Tools & actions
Prefer the **condensed** tool; it takes `action` + a `params_json` **JSON string**
whose keys are passed straight to the client method.

| Condensed tool | Actions |
|----------------|---------|
| `lgtm_mcp_alertmanager` | `get_status`, `get_receivers`, `get_alerts`, `get_alert_groups`, `get_silences`, `get_silence`, `post_silences`, `create_silence`, `delete_silence`, `post_alerts`, `create_alerts` |
| `lgtm_ingest_alerts` | (KG) list alerts + push `:Alert`/`:Receiver` nodes |

### Key parameters
- `get_alerts` — `active`, `silenced`, `inhibited`, `unprocessed` (bools); `filter`
  (list of `label=value` matcher strings); `receiver` (regex).
- `create_silence` — `matchers` (list), `starts_at`, `ends_at` (ISO-8601),
  `comment`, `created_by`.
- `get_silence` / `delete_silence` — `silence_id`.

## Recipes (`params_json`)
List active critical alerts:
```json
{"active":true,"silenced":false,"inhibited":false,"filter":["severity=critical"]}
```
Silence an alert for 2 hours during maintenance:
```json
{"matchers":[{"name":"alertname","value":"HighCPU","isRegex":false}],"starts_at":"2026-07-04T00:00:00Z","ends_at":"2026-07-04T02:00:00Z","comment":"planned maintenance","created_by":"ops"}
```
Delete a silence:
```json
{"silence_id":"<uuid>"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- Matchers for `create_silence` are objects (`name`/`value`/`isRegex`), while the
  `filter` param on reads is a list of `"name=value"` **strings** — different shapes.
- `starts_at`/`ends_at` must be RFC-3339/ISO-8601 UTC timestamps.
- An alert's stable id is its `fingerprint`; the KG node id is
  `observability:alert:<fingerprint>`.

## Related
- `lgtm-grafana-dashboards` — the Grafana half of this package.
- `lgtm_ingest_alerts` pushes alerts into the KG; `get_alerts` also auto-ingests on
  every read (best-effort, no-op without a reachable engine).
