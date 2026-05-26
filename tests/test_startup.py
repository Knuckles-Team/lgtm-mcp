import pytest


@pytest.mark.concept("LGTM-002")
def test_startup():
    # Basic import test
    import lgtm_mcp

    assert lgtm_mcp.__version__ == "0.15.0"
