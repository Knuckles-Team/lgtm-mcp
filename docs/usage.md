# Usage — API / MCP

`lgtm-mcp` exposes the same capability two ways: as **MCP tools** an agent calls, and
as a **Python API** (`Api`) you import. A deeper architectural description is in
[Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers two action-dispatch tools. Each
takes an `action` plus a `params_json` string of arguments matching the underlying
client method:

| Tool | Tag | Actions |
|---|---|---|
| `lgtm_mcp_alertmanager` | `alertmanager` | `get_status`, `get_receivers`, `get_silences`, `post_silences`, `create_silence`, `get_silence`, `delete_silence`, `get_alerts`, `post_alerts`, `create_alerts`, `get_alert_groups` |
| `lgtm_mcp_grafana` | `grafana` | `get_dashboards`, `create_dashboard`, `query_datasource` |

Example agent prompts that map onto these tools:

- *"List the alerts currently firing in Alertmanager"* → `lgtm_mcp_alertmanager` with `action=get_alerts`
- *"Silence the `HighLatency` alert for two hours"* → `lgtm_mcp_alertmanager` with `action=create_silence`
- *"What Grafana dashboards exist?"* → `lgtm_mcp_grafana` with `action=get_dashboards`

This MCP server also supports dynamic toolset selection and tag visibility filtering
at runtime (via `--tools` / `--toolsets`, the `MCP_ENABLED_TOOLS` family of
environment variables, or HTTP request headers / query parameters) so the exposed
surface can be narrowed to fit an agent's context budget.

## As a Python API

`Api` is a dynamic facade composed from the Alertmanager and Grafana clients. Build it
from the environment and call the read methods directly:

```python
from lgtm_mcp.api_client import Api

api = Api()        # reads ALERTMANAGER_URL / GRAFANA_URL / LGTM_TOKEN from the environment

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
