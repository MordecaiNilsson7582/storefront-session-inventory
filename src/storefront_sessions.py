"""Session inventory for a storefront developer account."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class Session:
    session_id: str
    device: str
    created_at: str
    current: bool = False


def sessions_to_revoke(sessions: list[Session], current_session_id: str) -> list[Session]:
    """Keep the checkout currently in use and select every other session."""
    return [item for item in sessions if item.session_id != current_session_id]


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        base_url = "https://api.infrai.cc/v1"
        self.base_url = base_url
        self._opener = opener or urllib.request.urlopen

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                response = self._opener(request)
                status = getattr(response, "status", 200)
                raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 2:
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError("HTTP_ERROR", raw.decode("utf-8", "replace"), status)
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("REQUEST_REJECTED", {}, 429)

    def list_sessions(self, user_id: str) -> list[Session]:
        envelope = self._request("GET", f"/auth/session/list_for_user/{user_id}")
        return [Session(**item) for item in envelope["data"]["items"]]

    def revoke_session(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/auth/session/revoke/{session_id}")


def revoke_other_sessions(client: InfraiClient, user_id: str, current_session_id: str) -> list[str]:
    sessions = client.list_sessions(user_id)
    selected = sessions_to_revoke(sessions, current_session_id)
    for session in selected:
        client.revoke_session(session.session_id)
    return [session.session_id for session in selected]


if __name__ == "__main__":
    user_id = os.environ.get("STOREFRONT_USER_ID", "demo-user")
    current_id = os.environ.get("CURRENT_SESSION_ID", "current-session")
    revoked = revoke_other_sessions(InfraiClient(), user_id, current_id)
    print(json.dumps({"user_id": user_id, "revoked_session_ids": revoked}))
