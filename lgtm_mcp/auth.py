"""CONCEPT:LGTM-003 Identity credentials loader and session manager."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting

from lgtm_mcp.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Get authenticated client for lgtm_mcp."""
    base_url = setting("ALERTMANAGER_URL") or setting("LGTM_MCP_BASE_URL", "")
    grafana_url = setting("GRAFANA_URL") or setting("LGTM_MCP_BASE_URL", "")
    token = setting("LGTM_TOKEN", "")
    username = setting("LGTM_MCP_USERNAME", "")
    password = setting("LGTM_MCP_PASSWORD", "")
    verify = setting("LGTM_MCP_SSL_VERIFY", True)

    if not base_url:
        # Default fallback for testing
        base_url = "http://localhost"
    if not grafana_url:
        grafana_url = "http://localhost"

    return Api(
        base_url=base_url,
        token=token,
        username=username,
        password=password,
        verify=verify,
        grafana_url=grafana_url,
    )
