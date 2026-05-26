import pytest


@pytest.mark.concept("LGTM-001")
def test_api_client_basic_mock(mock_ctx):
    """CONCEPT:LGTM-001 Test basic mock initialization of client facade."""
    assert mock_ctx is not None
    assert hasattr(mock_ctx, "info")


@pytest.mark.concept("LGTM-001")
def test_api_client_endpoints(mock_ctx):
    """CONCEPT:LGTM-001 Verify endpoint configuration on dynamic client."""
    from lgtm_mcp.auth import get_client

    client = get_client()
    assert client is not None
    assert hasattr(client, "request")


@pytest.mark.concept("LGTM-001")
def test_new_endpoints_exist_and_route():
    """CONCEPT:LGTM-001 Verify new Alertmanager and Grafana endpoints and routing logic."""
    from unittest.mock import MagicMock

    from lgtm_mcp.api_client import Api

    client = Api(
        base_url="http://alertmanager:9093",
        grafana_url="http://grafana:3000",
    )

    # Mock the internal requests session
    client._session.request = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"
    mock_response.json.return_value = {"status": "success"}
    client._session.request.return_value = mock_response

    # Test status endpoint
    client.get_status()
    client._session.request.assert_called_with(
        method="GET",
        url="http://alertmanager:9093/api/v2/status",
        headers={"Content-Type": "application/json"},
        params=None,
        json=None,
    )

    # Test query_datasource (Grafana endpoint)
    client.query_datasource(1, "SELECT *")
    client._session.request.assert_called_with(
        method="POST",
        url="http://grafana:3000/api/tsdb/query",
        headers={"Content-Type": "application/json"},
        params=None,
        json={
            "queries": [{"datasourceId": 1, "rawSql": "SELECT *", "format": "table"}]
        },
    )
