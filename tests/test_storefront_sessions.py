import json

from storefront_sessions import InfraiClient, Session, sessions_to_revoke


def test_checkout_session_is_kept_when_signing_out_other_devices():
    sessions = [
        Session("checkout-1", "Chrome on laptop", "2026-09-12T08:00:00Z"),
        Session("phone-2", "Safari on phone", "2026-09-11T18:30:00Z"),
    ]

    selected = sessions_to_revoke(sessions, "checkout-1")

    assert [item.session_id for item in selected] == ["phone-2"]


def test_list_sessions_decodes_live_items_envelope():
    class Response:
        status = 200

        def read(self):
            return json.dumps({"ok": True, "data": {"items": [
                {"session_id": "checkout-1", "device": "Chrome on laptop", "created_at": "2026-09-12T08:00:00Z"}
            ]}}).encode()

    client = InfraiClient(api_key="test-key", opener=lambda request: Response())

    assert client.list_sessions("probe-user") == [
        Session("checkout-1", "Chrome on laptop", "2026-09-12T08:00:00Z")
    ]
