"""Source-connector contributions for lgtm-mcp (CONCEPT:AU-KG.ingest.mcp-tool-connector).

Data-only subpackage: it carries ``mcp_source_presets.json`` — Tier-1 ``mcp_tool``
source presets the agent-utilities hub federates in via the
``agent_utilities.source_connector_providers`` entry-point. It holds no business logic
so the hub can resolve it cheaply.
"""
