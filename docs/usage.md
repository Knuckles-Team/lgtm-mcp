# Usage — API / MCP

`lgtm-mcp` exposes the same capability two ways: as **MCP tools** an agent calls, and
as a **Python API** (`Api`) the operator import. A deeper architectural description is in
[Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers one typed tool per Alertmanager
and Grafana operation, each taking its arguments by name:

| Area | Tools |
|---|---|
| Alertmanager | `lgtm_get_status`, `lgtm_get_receivers`, `lgtm_get_silences`, `lgtm_post_silences`, `lgtm_create_silence`, `lgtm_get_silence`, `lgtm_delete_silence`, `lgtm_get_alerts`, `lgtm_post_alerts`, `lgtm_create_alerts`, `lgtm_get_alert_groups` |
| Grafana | `lgtm_get_dashboards`, `lgtm_create_dashboard`, `lgtm_query_datasource` |
| Knowledge graph | `lgtm_ingest_alerts`, `lgtm_ingest_dashboards` |

Example agent prompts that map onto these tools:

- *"List the alerts currently firing in Alertmanager"* → `lgtm_get_alerts`
- *"Silence the `HighLatency` alert for two hours"* → `lgtm_create_silence`
- *"What Grafana dashboards exist?"* → `lgtm_get_dashboards`

This MCP server also supports dynamic toolset selection and tag visibility filtering
at runtime (via `--tools` / `--toolsets`, the `MCP_ENABLED_TOOLS` family of
environment variables, or HTTP request headers / query parameters) so the exposed
surface can be narrowed to fit an agent's context budget.

## As a Python API

`Api` is a dynamic facade composed from the Alertmanager and Grafana clients. Build it
from the environment and call the read methods directly:

```python
from lgtm_mcp.api_client import Api

api = Api()  # reads ALERTMANAGER_URL / GRAFANA_URL / LGTM_TOKEN from the environment

# Alertmanager reads
status = api.get_status()
alerts = api.get_alerts()
silences = api.get_silences()
groups = api.get_alert_groups()

# Grafana reads
dashboards = api.get_dashboards()
```

### Writes

Mutating operations create silences, post alerts, and provision dashboards:

```python
# Silence an alert for two hours
silence = api.create_silence(
    matchers=[{"name": "alertname", "value": "HighLatency", "isRegex": False}],
    duration_hours=2,
)

# Push alerts into Alertmanager
api.create_alerts([{"labels": {"alertname": "SyntheticCheck"}}])

# Provision a dashboard in Grafana
api.create_dashboard({"dashboard": {"title": "Service Health"}, "overwrite": True})
```
