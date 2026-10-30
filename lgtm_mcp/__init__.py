"""CONCEPT:AU-ECO.messaging.native-backend-abstraction Unified ecosystem initialization dynamic check."""

from scion_sdk.connector import Connector

from lgtm_mcp.api_client import Api
from lgtm_mcp.auth import get_client

connector = Connector(
    api=Api,
    get_client=get_client,
    tools="lgtm_mcp.mcp_server",
    instructions="LGTM MCP MCP Server - Managed dynamic operations.",
    transports=(
        "stdio",
        "streamable-http",
    ),
)
