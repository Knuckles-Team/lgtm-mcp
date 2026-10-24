"""CONCEPT:LG-OS.governance.lgtm Dynamic client facade orchestration and resource mappings."""

#!/usr/bin/env python
from lgtm_mcp.api.api_client_alertmanager import Api as AlertmanagerApi
from lgtm_mcp.api.api_client_grafana import Api as GrafanaApi


class Api(AlertmanagerApi, GrafanaApi):
    pass
