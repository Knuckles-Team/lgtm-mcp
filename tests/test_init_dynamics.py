import pytest
@pytest.mark.concept("LGTM-001")
def test_init_dynamics():
    import lgtm_mcp

    assert lgtm_mcp._MCP_AVAILABLE is True
