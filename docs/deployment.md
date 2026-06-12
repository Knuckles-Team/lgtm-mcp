# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`lgtm-mcp` exposes its MCP server (console script `lgtm-mcp`) four ways. Pick the row that
matches where the server runs relative to your MCP client, then copy the matching
`mcp_config.json` below. Replace the `<your-…>` placeholders with the values from the **Configuration / Environment Variables** section.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

The client launches the server over stdio via `uvx` — best for local IDEs
(Cursor, Claude Desktop, VS Code):

```json
{
  "mcpServers": {
    "lgtm-mcp": {
      "command": "uvx",
      "args": ["--from", "lgtm-mcp", "lgtm-mcp"],
      "env": {
        "ALERTMANAGER_URL": "<your-alertmanager_url>",
        "GRAFANA_URL": "<your-grafana_url>",
        "LGTM_TOKEN": "<your-lgtm_token>"
      }
    }
  }
}
```

### 2. Streamable-HTTP (local process)

Run the server as a long-lived HTTP process:

```bash
uvx --from lgtm-mcp lgtm-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Then either let the client launch it:

```json
{
  "mcpServers": {
    "lgtm-mcp": {
      "command": "uvx",
      "args": ["--from", "lgtm-mcp", "lgtm-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "ALERTMANAGER_URL": "<your-alertmanager_url>",
        "GRAFANA_URL": "<your-grafana_url>",
        "LGTM_TOKEN": "<your-lgtm_token>"
      }
    }
  }
}
```

…or connect to the already-running process by URL:

```json
{
  "mcpServers": {
    "lgtm-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

**(a) Launch a container directly from `mcp_config.json`** (stdio over the container —
no ports to manage). Swap `docker` for `podman` for a daemonless runtime:

```json
{
  "mcpServers": {
    "lgtm-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "-e", "ALERTMANAGER_URL=<your-alertmanager_url>",
        "-e", "GRAFANA_URL=<your-grafana_url>",
        "-e", "LGTM_TOKEN=<your-lgtm_token>",
        "knucklessg1/lgtm-mcp:latest"
      ]
    }
  }
}
```

**(b) Run a local streamable-http container, then connect by URL:**

```bash
docker run -d --name lgtm-mcp -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  -e ALERTMANAGER_URL="<your-alertmanager_url>" \
  -e GRAFANA_URL="<your-grafana_url>" \
  -e LGTM_TOKEN="<your-lgtm_token>" \
  knucklessg1/lgtm-mcp:latest
# or, from a clone of this repo:
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "lgtm-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

**(c) From a local checkout with `uv`:**

```bash
uv run lgtm-mcp --transport streamable-http --port 8000
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely (e.g. as a Docker service) and published through
Caddy on the internal `*.arpa` zone, connect with the `"url"` key — no local process or
image required:

```json
{
  "mcpServers": {
    "lgtm-mcp": { "url": "http://lgtm-mcp.arpa/mcp" }
  }
}
```

Caddy reverse-proxies `http://lgtm-mcp.arpa` to the container's `:8000`
streamable-http listener; `http://lgtm-mcp.arpa/health` returns
`{"status":"OK"}` when the service is live.
<!-- END GENERATED: deployment-options -->

This page covers running `lgtm-mcp` as a long-lived server: the transports, a Docker
Compose stack, putting it behind a Caddy reverse proxy, and giving it a DNS name with
Technitium. To provision the **LGTM observability stack** it connects to, see
[Backing Platform](platform.md).

> `lgtm-mcp` ships both an **MCP server** (console script `lgtm-mcp`) and a Pydantic-AI
> **agent server** (console script `lgtm-agent`). The MCP server is a typed,
> deterministic tool surface a policy router or agent calls; the agent server connects
> to that surface to deliver a conversational interface. The agent section is
> documented at the end of this page.

## Run the MCP server

The transport is selected with `--transport` (or the `TRANSPORT` env var):

=== "stdio (default)"

    ```bash
    lgtm-mcp
    ```
    For IDE / desktop MCP clients that launch the server as a subprocess.

=== "streamable-http"

    ```bash
    lgtm-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```
    A network server with a `/health` endpoint and `/mcp` route.

=== "sse"

    ```bash
    lgtm-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Configuration (environment)

`lgtm-mcp` is configured entirely from the environment. The **required** set:

| Var | Default | Meaning |
|---|---|---|
| `ALERTMANAGER_URL` | `http://localhost:9093` | Prometheus Alertmanager API URL |
| `GRAFANA_URL` | `http://localhost:3000` | Grafana API endpoint |
| `LGTM_TOKEN` | _(none)_ | Grafana admin API key or service token |

Plus `HOST` / `PORT` / `TRANSPORT` for HTTP transports. The full set is documented in
[`.env.example`](https://github.com/Knuckles-Team/lgtm-mcp/blob/main/.env.example).
Copy it to `.env` and fill in your service endpoints before starting the server.

## Docker Compose

The repo ships [`docker/mcp.compose.yml`](https://github.com/Knuckles-Team/lgtm-mcp/blob/main/docker/mcp.compose.yml).
It reads a sibling `.env` and publishes the HTTP server on `:8000`:

```yaml
services:
  lgtm-mcp:
    image: knucklessg1/lgtm-mcp:latest
    container_name: lgtm-mcp
    hostname: lgtm-mcp
    restart: always
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TRANSPORT=streamable-http
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
cp .env.example .env          # then edit GRAFANA_URL / ALERTMANAGER_URL / LGTM_TOKEN
docker compose -f docker/mcp.compose.yml up -d
docker compose -f docker/mcp.compose.yml logs -f
```

## Behind a Caddy reverse proxy

Expose the HTTP server on a hostname with automatic TLS. Add to your `Caddyfile`:

```caddy
# Internal (self-signed) — homelab .arpa zone
lgtm-mcp.arpa {
    tls internal
    reverse_proxy lgtm-mcp:8000
}
```

```caddy
# Public — automatic Let's Encrypt
lgtm-mcp.example.com {
    reverse_proxy lgtm-mcp:8000
}
```

Reload Caddy:

```bash
docker compose -f services/caddy/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## DNS with Technitium

Point the hostname at the host running Caddy. Via the Technitium API:

```bash
curl -s "http://technitium.arpa:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=lgtm-mcp.arpa" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=10.0.0.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `lgtm-mcp.arpa → <caddy-host-ip>` in the Technitium web
console (`http://technitium.arpa:5380`). The ecosystem
[`technitium-dns-mcp`](https://knuckles-team.github.io/technitium-dns-mcp/) automates
this as a tool.

## Register with an MCP client

Add to your client's `mcp_config.json` (multiplexer nickname `lgtm`):

```json
{
  "mcpServers": {
    "lgtm-mcp": {
      "command": "uv",
      "args": ["run", "lgtm-mcp"],
      "env": {
        "GRAFANA_URL": "http://your-grafana:3000",
        "ALERTMANAGER_URL": "http://your-alertmanager:9093",
        "LGTM_TOKEN": "your_grafana_api_token"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://lgtm-mcp.arpa/mcp` instead.

## Agent server

`lgtm-mcp` also ships a Pydantic-AI **agent server** (console script `lgtm-agent`)
that connects to the MCP tool surface and exposes a conversational endpoint. It is
built on the `agent-utilities` agent runtime and is installed with the `agent` extra:

```bash
pip install "lgtm-mcp[agent]"
```

Run it, pointing it at a running MCP server with `--mcp-url` (or wire it to a local
`mcp_config.json` with `--mcp-config`):

```bash
lgtm-agent --mcp-url http://lgtm-mcp.arpa/mcp --host 0.0.0.0 --port 8080
```

| Flag / Var | Meaning |
|---|---|
| `--mcp-url` | URL of the running MCP server the agent attaches to |
| `--mcp-config` | Path to an `mcp_config.json` (defaults to `mcp_config.json`) |
| `--host` / `--port` | Bind address for the agent HTTP server |
| `--provider` / `--model-id` | LLM provider and model identifier |

To run the agent in Docker, build from the repository and start the `lgtm-agent`
entrypoint, setting `MCP_URL` to the MCP server endpoint. Place both the MCP server
and the agent on the same Docker network so the agent reaches the server by container
name (for example `http://lgtm-mcp:8000/mcp`).
