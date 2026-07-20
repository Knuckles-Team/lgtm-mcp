# Provider workflow catalog

Load only the workflow relevant to the current request.

- [lgtm-alertmanager-alerts](../../lgtm-alertmanager-alerts/WORKFLOW.md): Alertmanager alert and silence operations over the lgtm-mcp MCP server — list active/silenced alerts and alert groups, read cluster status and receivers, and create/read/delete silences to mute noisy alerts. Use when the agent must triage firing alerts, understand routing/receivers, or silence an alert during maintenance. Do NOT use for Grafana dashboards or datasource queries (use lgtm-grafana-dashboards).
- [lgtm-grafana-dashboards](../../lgtm-grafana-dashboards/WORKFLOW.md): Grafana dashboard and datasource operations over the lgtm-mcp MCP server — search existing dashboards, create a dashboard from a JSON model, and run ad-hoc queries against a Grafana datasource (Prometheus/Loki/etc.). Use when the agent must discover what dashboards exist, provision a new dashboard, or pull metric/log data through Grafana's datasource proxy. Do NOT use for Alertmanager alert/silence lifecycle (use lgtm-alertmanager-alerts) or for raw Prometheus HTTP outside Grafana.
