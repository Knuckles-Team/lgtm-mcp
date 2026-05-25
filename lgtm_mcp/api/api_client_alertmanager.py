from lgtm_mcp.api.api_client_base import ApiClientBase

class Api(ApiClientBase):
    def get_alerts(self) -> list:
        """Get active alerts."""
        return self.request("GET", "/api/v2/alerts")

    def create_silence(self, matchers: list, starts_at: str, ends_at: str, comment: str, created_by: str) -> dict:
        """Silence active alerts."""
        return self.request("POST", "/api/v2/silences", data={
            "matchers": matchers,
            "startsAt": starts_at,
            "endsAt": ends_at,
            "comment": comment,
            "createdBy": created_by
        })

    def delete_silence(self, silence_id: str) -> dict:
        """Delete silence rule."""
        return self.request("DELETE", f"/api/v2/silence/{silence_id}")

    def get_status(self) -> dict:
        """Get alertmanager system status."""
        return self.request("GET", "/api/v2/status")
