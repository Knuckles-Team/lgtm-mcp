"""Action-discovery standardization tests.
CONCEPT:LG-OS.governance.lgtm-2
"""

import pytest
from agent_utilities.mcp_utilities import resolve_action

from lgtm_mcp.mcp_server import ALERTMANAGER_ACTIONS, GRAFANA_ACTIONS


@pytest.mark.concept("LG-OS.governance.lgtm-2")
@pytest.mark.parametrize("actions", [ALERTMANAGER_ACTIONS, GRAFANA_ACTIONS])
def test_list_actions_returns_names(actions):
    """CONCEPT:LG-OS.governance.lgtm-2 Discovery keyword returns the bounded action set."""
    payload = resolve_action("list_actions", actions, service="lgtm-mcp")
    assert isinstance(payload, dict)
    assert payload["service"] == "lgtm-mcp"
    assert set(payload["actions"]) == set(actions)


@pytest.mark.concept("LG-OS.governance.lgtm-2")
@pytest.mark.parametrize("actions", [ALERTMANAGER_ACTIONS, GRAFANA_ACTIONS])
def test_bogus_action_raises_with_did_you_mean(actions):
    """CONCEPT:LG-OS.governance.lgtm-2 Unknown action raises a rich error mentioning list_actions."""
    with pytest.raises(ValueError) as exc:
        resolve_action("definitely_not_a_real_action", actions, service="lgtm-mcp")
    assert "list_actions" in str(exc.value)


@pytest.mark.concept("LG-OS.governance.lgtm-2")
def test_plural_alias_resolves_to_singular():
    """CONCEPT:LG-OS.governance.lgtm-2 Canonical pass-through for a known action."""
    assert (
        resolve_action("get_status", ALERTMANAGER_ACTIONS, service="lgtm-mcp")
        == "get_status"
    )
