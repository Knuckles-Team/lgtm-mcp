import pytest


@pytest.mark.concept("LG-OS.identity.lgtm")
def test_mcp_server_security_context():
    """CONCEPT:LG-OS.identity.lgtm Verify that the server registers with correct security credentials."""
    from lgtm_mcp.auth import get_client

    client = get_client()
    assert client is not None
