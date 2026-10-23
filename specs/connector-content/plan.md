# CONN-LGTM-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `lgtm-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `lgtm_mcp` from it.
