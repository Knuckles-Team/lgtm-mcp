---
name: lgtm-alertmanager-alerts
skill_type: skill
description: >-
  Alertmanager alert and silence operations over the lgtm-mcp MCP server — list active/silenced alerts and alert groups, read cluster status and receivers, and create/read/delete silences to mute noisy alerts. Use when the agent must triage firing alerts, understand routing/receivers, or silence an alert during maintenance.
license: MIT
tags: [lgtm, alertmanager, alerts, silences, observability, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# LGTM Alertmanager Alerts

Scope: Alertmanager alert and silence operations over the lgtm-mcp MCP server — list active/silenced alerts and alert groups, read cluster status and receivers, and create/read/delete silences to mute noisy alerts. Use when the agent must triage firing alerts, understand routing/receivers, or silence an alert during maintenance. Do NOT use for Grafana dashboards or datasource queries (use lgtm-grafana-dashboards).

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


## Steps

1. Check connectivity with `lgtm_get_status`, and verify it returns cluster status rather than an auth or connection error.
2. Triage with `lgtm_get_alerts`(`active`, `silenced`, `inhibited`, `filter`), and verify the response lists alerts with `fingerprint` values.
3. Inspect routing with `lgtm_get_alert_groups` and `lgtm_get_receivers`, and verify each alert maps to a receiver.
4. Silence only when asked: call `lgtm_create_silence`(`matchers`, `starts_at`, `ends_at`, `comment`, `created_by`), and verify the returned silence id appears in `lgtm_get_silences`.
5. Expire a silence with `lgtm_delete_silence`(`silence_id`), and verify `lgtm_get_silence` shows it expired.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Authentication or connection error | `ALERTMANAGER_URL` or credentials (`LGTM_TOKEN`, or `LGTM_MCP_USERNAME` with `LGTM_MCP_PASSWORD`) missing | Set `ALERTMANAGER_URL` and one credential form, then call `lgtm_get_status` again |
| Silence rejected | `matchers` given as strings or timestamps not RFC-3339 UTC | Pass matchers as objects with `name`, `value`, `isRegex`, and UTC timestamps such as `2026-07-04T00:00:00Z` |
| Empty alert list | `filter` too narrow or states excluded | Pass `filter` as `name=value` strings and set `active`, `silenced`, `inhibited` as intended |

## Tools
One typed tool per operation; pass each argument by name.

| Tool | Use |
|------|-----|
| `lgtm_get_status`, `lgtm_get_receivers` | Alertmanager status and its receivers |
| `lgtm_get_alerts`, `lgtm_get_alert_groups` | Read alerts, or alerts grouped by route |
| `lgtm_get_silences`, `lgtm_get_silence` | Read silences |
| `lgtm_create_silence`, `lgtm_post_silences`, `lgtm_delete_silence` | Create, update or expire a silence |
| `lgtm_create_alerts`, `lgtm_post_alerts` | Post alerts to Alertmanager |
| `lgtm_ingest_alerts` | List alerts and push `:Alert`/`:Receiver` nodes into the knowledge graph |

## Recipes (tool arguments)
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
- Matchers for `create_silence` are objects (`name`/`value`/`isRegex`), while the
  `filter` param on reads is a list of `"name=value"` **strings** — different shapes.
- `starts_at`/`ends_at` must be RFC-3339/ISO-8601 UTC timestamps.
- An alert's stable id is its `fingerprint`; the KG node id is
  `observability:alert:<fingerprint>`.

## Related
- `lgtm-grafana-dashboards` — the Grafana half of this package.
- `lgtm_ingest_alerts` pushes alerts into the KG; `get_alerts` also auto-ingests on
  every read (best-effort, no-op without a reachable engine).
