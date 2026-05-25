from lgtm_mcp.api.api_client_base import ApiClientBase


class Api(ApiClientBase):
    def get_dashboards(self) -> list:
        """Get Grafana dashboards."""
        return self.request("GET", "/api/search")

    def create_dashboard(self, dashboard_data: dict) -> dict:
        """Create dashboard."""
        return self.request("POST", "/api/dashboards/db", data=dashboard_data)

    def query_datasource(self, datasource_id: int, query: str) -> dict:
        """Query a datasource."""
        return self.request(
            "POST",
            "/api/tsdb/query",
            data={
                "queries": [
                    {"datasourceId": datasource_id, "rawSql": query, "format": "table"}
                ]
            },
        )
