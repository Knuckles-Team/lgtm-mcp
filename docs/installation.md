# Installation

`lgtm-mcp` is a standard Python package and a prebuilt container image. Pick the path
that matches how you want to run it.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable **Grafana** instance and/or **Prometheus Alertmanager** — see
  [Backing Platform](platform.md) to deploy the LGTM stack locally.

## From PyPI (recommended)

```bash
pip install lgtm-mcp
```

### Optional extras

The base install is intentionally minimal. Install the extra for what you need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "lgtm-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "lgtm-mcp[agent]"` | Pydantic-AI agent + Logfire tracing (`agent-utilities[agent,logfire]`) |
| `all` | `pip install "lgtm-mcp[all]"` | Everything above |
| `test` | `pip install "lgtm-mcp[test]"` | `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist` |

```bash
# Typical: run the MCP server and the agent server
pip install "lgtm-mcp[all]"
```

## From source

```bash
git clone https://github.com/Knuckles-Team/lgtm-mcp.git
cd lgtm-mcp
pip install -e ".[all]"          # editable install with every extra
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[all]"
uv run lgtm-mcp
```

## Prebuilt Docker image

A multi-stage, slim image is published on every release (entrypoint `lgtm-mcp`):

```bash
docker pull knucklessg1/lgtm-mcp:latest

docker run --rm -i \
  -e GRAFANA_URL=http://your-grafana:3000 \
  -e ALERTMANAGER_URL=http://your-alertmanager:9093 \
  -e LGTM_TOKEN=your_grafana_api_token \
  knucklessg1/lgtm-mcp:latest        # stdio transport (default)
```

For an HTTP server with a published port, see [Deployment](deployment.md).

## Verify the install

```bash
lgtm-mcp --help
python -c "import lgtm_mcp; print(lgtm_mcp.__version__)"
```

## Next steps

- **[Deployment](deployment.md)** — run it as a long-lived MCP server behind Caddy + DNS.
- **[Usage](usage.md)** — call the tools and the `Api` client.
- **[Configuration](deployment.md#configuration-environment)** — every environment variable.
