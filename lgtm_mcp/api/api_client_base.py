from typing import Any
from urllib.parse import urljoin

import requests
import urllib3


class ApiClientBase:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify: bool = True,
        grafana_url: str | None = None,
    ):
        import os

        self.base_url = base_url
        self.alertmanager_url = base_url
        self.grafana_url = grafana_url or os.getenv("GRAFANA_URL") or base_url
        self.token = token
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._session.verify = verify

        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if token:
            self._session.headers.update({"Authorization": f"Bearer {token}"})
        elif username and password:
            self._session.auth = (username, password)

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
    ) -> Any:
        if endpoint.startswith("http"):
            url = endpoint
        else:
            base = (
                self.alertmanager_url
                if endpoint.startswith("/api/v2")
                else self.grafana_url
            )
            url = urljoin(base, endpoint)

        headers = {"Content-Type": "application/json"}
        response = self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
        )

        if response.status_code >= 400:
            raise Exception(f"API error: {response.status_code} - {response.text}")

        if response.status_code == 204 or not response.text.strip():
            return {"status": "success"}

        try:
            return response.json()
        except Exception:
            return {"status": "success", "text": response.text}
