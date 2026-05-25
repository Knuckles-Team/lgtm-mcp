#!/usr/bin/env python
from lgtm_mcp.api.api_client_base import ApiClientBase
from lgtm_mcp.api.api_client_alertmanager import Api as AlertmanagerApi
from lgtm_mcp.api.api_client_grafana import Api as GrafanaApi

__version__ = "0.15.0"

class Api(AlertmanagerApi, GrafanaApi):
    pass
