import pytest

@pytest.mark.concept("LGTM-001")
def test_api_client_basic_mock(mock_ctx):
    """CONCEPT:LGTM-001 Test basic mock initialization of client facade."""
    assert mock_ctx is not None
    assert mock_ctx.get("env_check") is True

@pytest.mark.concept("LGTM-001")
def test_api_client_endpoints(mock_ctx):
    """CONCEPT:LGTM-001 Verify endpoint configuration on dynamic client."""
    from lgtm_mcp.api_client import Api
    from lgtm_mcp.auth import get_client
    
    client = get_client()
    assert client is not None
    assert hasattr(client, "request")
