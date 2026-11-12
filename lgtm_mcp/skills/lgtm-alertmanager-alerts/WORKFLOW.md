# Lgtm Alertmanager Alerts

Alertmanager alert and silence operations over the lgtm-mcp MCP server — list active/silenced alerts and alert groups, read cluster status and receivers, and create/read/delete silences to mute noisy alerts. Use when the agent must triage firing alerts, understand routing/receivers, or silence an alert during maintenance. Do NOT use for Grafana dashboards or datasource queries (use lgtm-grafana-dashboards).

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
| `LGTM_TLS_PROFILE` | optional | Named AgentConfig TLS profile; peer and hostname verification are mandatory. |
| `LGTM_TLS_PROFILE_REF` | optional | Reference-backed AgentConfig TLS profile selector. |


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
