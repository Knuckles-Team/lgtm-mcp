# lgtm-mcp

LGTM observability **API + MCP server** for the agent-utilities ecosystem — typed,
deterministic tools over Grafana and Prometheus Alertmanager for agentic alerting,
silencing, and dashboard operations.

!!! info "Official documentation"
    This site is the canonical reference for `lgtm-mcp`, maintained alongside every
    release.

[![PyPI](https://img.shields.io/pypi/v/lgtm-mcp)](https://pypi.org/project/lgtm-mcp/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/lgtm-mcp)](https://github.com/Knuckles-Team/lgtm-mcp/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/lgtm-mcp)

## Overview

`lgtm-mcp` wraps the **Grafana** and **Prometheus Alertmanager** REST surfaces with
typed, deterministic MCP tools, so an agent can read firing alerts, manage silences,
and operate dashboards without handling HTTP transport directly. It provides:

- **`Api`** — a dynamic facade (`lgtm_mcp.api_client.Api`) composed from the
  Alertmanager and Grafana clients, with credential authentication and SSL handling.
- **Action-dispatch MCP tools** — `lgtm_mcp_alertmanager` and `lgtm_mcp_grafana`,
  each routing a named action to the underlying client method.
- **An optional agent server** — a Pydantic-AI agent (`lgtm-agent`) that connects to
  the MCP tool surface for conversational observability operations.

The server remains inactive when credentials are absent, degrading safely rather than
raising on an unreachable backend.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP server, the agent server, Docker Compose, Caddy + Technitium.
- :material-console: **[Usage](usage.md)** — the MCP tools and the `Api` Python client.
- :material-database-cog: **[Backing Platform](platform.md)** — deploy the LGTM observability stack with Docker.
- :material-sitemap: **[Overview](overview.md)** — architecture and the dynamic facade.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:LGTM-*` registry.

</div>

## Quick start

```bash
pip install "lgtm-mcp[mcp]"
lgtm-mcp                         # stdio MCP server (default transport)
```

Connect it to a Grafana / Alertmanager deployment:

```bash
export GRAFANA_URL=http://your-grafana:3000
export ALERTMANAGER_URL=http://your-alertmanager:9093
export LGTM_TOKEN=your_grafana_api_token
lgtm-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, reverse proxy, DNS).
