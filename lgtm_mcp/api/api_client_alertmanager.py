from typing import Any

from lgtm_mcp.api.api_client_base import ApiClientBase


class Api(ApiClientBase):
    def get_status(self) -> dict[str, Any]:
        """Get current status of an Alertmanager instance and its cluster."""
        return self.request("GET", "/api/v2/status")

    def get_receivers(
        self, receiver_matchers: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get list of all receivers (notification integrations)."""
        params = {}
        if receiver_matchers is not None:
            params["receiver_matchers"] = receiver_matchers
        return self.request("GET", "/api/v2/receivers", params=params)

    def get_silences(self, filter: list[str] | None = None) -> list[dict[str, Any]]:
        """Get a list of silences."""
        params = {}
        if filter is not None:
            params["filter"] = filter
        return self.request("GET", "/api/v2/silences", params=params)

    def post_silences(self, silence: dict[str, Any]) -> dict[str, Any]:
        """Post a new silence or update an existing one."""
        return self.request("POST", "/api/v2/silences", data=silence)

    def create_silence(
        self,
        matchers: list,
        starts_at: str,
        ends_at: str,
        comment: str,
        created_by: str,
    ) -> dict:
        """Silence active alerts (Helper method for backward compatibility)."""
        return self.post_silences(
            {
                "matchers": matchers,
                "startsAt": starts_at,
                "endsAt": ends_at,
                "comment": comment,
                "createdBy": created_by,
            }
        )

    def get_silence(self, silence_id: str) -> dict[str, Any]:
        """Get a silence by its ID."""
        return self.request("GET", f"/api/v2/silence/{silence_id}")

    def delete_silence(self, silence_id: str) -> dict[str, Any]:
        """Delete silence rule."""
        return self.request("DELETE", f"/api/v2/silence/{silence_id}")

    def get_alerts(
        self,
        active: bool = True,
        silenced: bool = True,
        inhibited: bool = True,
        unprocessed: bool = True,
        filter: list[str] | None = None,
        receiver: str | None = None,
        receiver_matchers: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get a list of alerts."""
        params: dict[str, Any] = {
            "active": active,
            "silenced": silenced,
            "inhibited": inhibited,
            "unprocessed": unprocessed,
        }
        if filter is not None:
            params["filter"] = filter
        if receiver is not None:
            params["receiver"] = receiver
        if receiver_matchers is not None:
            params["receiver_matchers"] = receiver_matchers
        return self.request("GET", "/api/v2/alerts", params=params)

    def post_alerts(self, alerts: list[dict[str, Any]]) -> dict[str, Any]:
        """Create new Alerts."""
        return self.request("POST", "/api/v2/alerts", data=alerts)

    def create_alerts(self, alerts: list[dict[str, Any]]) -> dict[str, Any]:
        """Create new Alerts (Helper method matching post_alerts)."""
        return self.post_alerts(alerts)

    def get_alert_groups(
        self,
        active: bool = True,
        silenced: bool = True,
        inhibited: bool = True,
        muted: bool = True,
        filter: list[str] | None = None,
        receiver: str | None = None,
        receiver_matchers: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get a list of alert groups."""
        params: dict[str, Any] = {
            "active": active,
            "silenced": silenced,
            "inhibited": inhibited,
            "muted": muted,
        }
        if filter is not None:
            params["filter"] = filter
        if receiver is not None:
            params["receiver"] = receiver
        if receiver_matchers is not None:
            params["receiver_matchers"] = receiver_matchers
        return self.request("GET", "/api/v2/alerts/groups", params=params)
