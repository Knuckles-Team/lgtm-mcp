---
name: lgtm-mcp-operations
skill_type: skill
description: >-
  Operate lgtm-mcp through its governed MCP and Arbora capabilities, including lgtm alertmanager alerts, lgtm grafana dashboards. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Lgtm Mcp Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Steps

1. Discover tools in the verified GraphSession and tenant with `find`(intent="alertmanager alerts"), and verify the tool names you plan to use are listed.
2. Inspect first with `lgtm_get_status` and `lgtm_get_alerts` or `lgtm_get_dashboards`, and verify the current state matches the request.
3. Run the approved change, such as `lgtm_create_silence` or `lgtm_create_dashboard`, after presenting its impact, and verify the response status.
4. For destructive actions such as `lgtm_delete_silence`, obtain explicit approval first, and verify the result with `lgtm_get_silences`.
5. Push state to the graph with `lgtm_ingest_alerts` or `lgtm_ingest_dashboards` only when asked, and verify the response reports ingested items.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Tool or schema not found | Stale tool name assumed | Rerun `find` for the operation and use the schema it returns |
| Request denied | Session or tenant lacks the needed scope | Stop and ask the operator for the scope, since ACL state is never bypassed |
| Connection error from `lgtm_get_status` | `ALERTMANAGER_URL` or `GRAFANA_URL` unset or wrong | Set the base URL and credentials named in the domain skill, then call `lgtm_get_status` again |

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.

## Tools by task

Every served tool is named below under the task it serves. Pass each argument by name.

- **check-alertmanager-health**: Read the Alertmanager status and its notification receivers. `lgtm_get_status`, `lgtm_get_receivers`
- **triage-firing-alerts**: List the alerts that are firing and the groups they route into. `lgtm_get_alerts`, `lgtm_get_alert_groups`
- **silence-an-alert**: Find matching alerts, create a time-boxed silence and expire it when the work is done. `lgtm_get_alerts`, `lgtm_create_silence`, `lgtm_get_silences`, `lgtm_get_silence`, `lgtm_post_silences`, `lgtm_delete_silence`
- **send-test-alert**: Post alerts to Alertmanager to test routing. `lgtm_create_alerts`, `lgtm_post_alerts`, `lgtm_get_alerts`
- **inspect-dashboards**: List dashboards and query the data source behind one. `lgtm_get_dashboards`, `lgtm_query_datasource`
- **publish-dashboard**: Create or overwrite a dashboard and confirm it by listing dashboards. `lgtm_create_dashboard`, `lgtm_get_dashboards`
- **ingest-observability-state**: Push alerts and dashboards into the knowledge graph. `lgtm_ingest_alerts`, `lgtm_ingest_dashboards`
