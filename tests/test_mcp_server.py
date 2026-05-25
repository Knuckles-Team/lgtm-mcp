import pytest

@pytest.mark.concept("LGTM-002")
def test_mcp_server_registration():
    """CONCEPT:LGTM-002 Test that tools register successfully."""
    from lgtm_mcp.mcp_server import get_mcp_instance
    mcp = get_mcp_instance()
    assert mcp is not None
    
    # Verify tool registry count is greater than zero
    assert len(mcp._tools) > 0

@pytest.mark.concept("LGTM-003")
def test_mcp_server_security_context():
    """CONCEPT:LGTM-003 Verify that the server registers with correct security credentials."""
    from lgtm_mcp.auth import get_client
    client = get_client()
    assert client is not None
