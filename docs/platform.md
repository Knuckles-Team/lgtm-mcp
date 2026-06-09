# Backing Platform — LGTM Observability Stack

`lgtm-mcp` is a **client** of a Grafana instance and a Prometheus Alertmanager. This
page provides a Docker recipe for deploying the observability stack locally to serve as
the target of `GRAFANA_URL` and `ALERTMANAGER_URL`. For production topologies, follow
the upstream [Grafana](https://grafana.com/docs/) and
[Prometheus](https://prometheus.io/docs/) documentation.

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack that mirrors [`services/`](https://github.com/Knuckles-Team).
    Systems offered only as a managed service have no local recipe.

## Single-node deployment (Compose)

The following stack runs Prometheus, Alertmanager, and Grafana from their official
public images. Prometheus scrapes targets and routes firing rules to Alertmanager;
Grafana provides dashboards on `:3000`.

```yaml
# docker/lgtm.compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    volumes:
      - prometheus_data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  alertmanager:
    image: prom/alertmanager:latest
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    volumes:
      - alertmanager_data:/alertmanager
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"            # Alertmanager API → ALERTMANAGER_URL

  grafana:
    image: grafana/grafana-oss:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"           # Grafana API → GRAFANA_URL

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

```bash
docker compose -f docker/lgtm.compose.yml up -d

# Confirm the endpoints answer
curl -s http://localhost:9093/api/v2/status     # Alertmanager
curl -s http://localhost:3000/api/health        # Grafana
```

A complete homelab stack — which adds Loki (logs), Tempo (traces), node-exporter, and
cAdvisor on a Swarm overlay network — is maintained in the ecosystem
[`services/lgtm`](https://github.com/Knuckles-Team) recipe.

## Connect lgtm-mcp

Point the connector at the deployed endpoints and supply a Grafana service token:

```bash
export GRAFANA_URL=http://localhost:3000
export ALERTMANAGER_URL=http://localhost:9093
export LGTM_TOKEN=your_grafana_api_token

lgtm-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

Create the Grafana token under **Administration → Service accounts** (or
**API keys**), then assign it to `LGTM_TOKEN`.

## Combined deployment

A combined stack places the observability backends and the MCP server on one Docker
network, so the server reaches Grafana and Alertmanager by container name:

```yaml
# docker/stack.compose.yml
services:
  alertmanager:
    image: prom/alertmanager:latest
    ports: ["9093:9093"]

  grafana:
    image: grafana/grafana-oss:latest
    ports: ["3000:3000"]

  lgtm-mcp:
    image: knucklessg1/lgtm-mcp:latest
    depends_on: [grafana, alertmanager]
    environment:
      - GRAFANA_URL=http://grafana:3000
      - ALERTMANAGER_URL=http://alertmanager:9093
      - LGTM_TOKEN=your_grafana_api_token
      - TRANSPORT=streamable-http
      - HOST=0.0.0.0
      - PORT=8000
    ports: ["8000:8000"]
```

```bash
docker compose -f docker/stack.compose.yml up -d
```
