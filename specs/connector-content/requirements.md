# CONN-LGTM-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-LGTM-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `lgtm-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. Caller chain: The `lgtm-mcp` console script runs `scion_sdk.cli:serve`, which loads the `scion_sdk.connector` entry point `lgtm-mcp = lgtm_mcp:connector` and builds the server from `lgtm_mcp/__init__.py::connector` (tools=`lgtm_mcp.mcp_server`, with `lgtm_mcp_grafana` and `lgtm_mcp_alertmanager`). Shape: No code change is expected beyond the declared `Connector` in `lgtm_mcp/__init__.py`; the missing test builds the server with `scion_sdk.connector.build_server` and lists resources and prompts, reusing `ConnectorContent.for_package` defaults from `scion_sdk.mcp.content`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Planned test: `tests/test_default_content_surfaces.py::test_default_content_lists_skill_and_ontology_resources_and_prompts`. |
