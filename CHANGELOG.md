# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.8] - 2026-11-12

### Changed
- The hand-written `action`-routed tools `lgtm_mcp_alertmanager` and `lgtm_mcp_grafana` are removed. Every Alertmanager and Grafana operation is served as one typed tool per client method (`lgtm_get_alerts`, `lgtm_create_silence`, `lgtm_get_dashboards`, ...); `lgtm_ingest_alerts` and `lgtm_ingest_dashboards` stay. The routed tools' implicit best-effort knowledge-graph ingest after `get_alerts` and `get_dashboards` is gone; call the ingest tools to push state.
- Declare tool-use contracts, prompt and skill links, data locations and business roles; ship an operator and two business-role agent prompts in place of the placeholder specialist prompt; root every ontology class in a core class.
- Require `scion-sdk>=0.9.0,<0.10.0`.

## [2.3.7] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [2.3.5] - 2026-10-26

### Added
- Add the packaged LGTM connector development skill and delivery contract.

## [2.3.4] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [0.15.0] - 2026-05-25
### Added
- Initial dynamic facade API client implementation.
- FastMCP server entry points and modular tools.
- Rich documentation templates, including standardized environment configuration.
- Complete test suite validating startup and facade execution.
- Standardized MIT License.
