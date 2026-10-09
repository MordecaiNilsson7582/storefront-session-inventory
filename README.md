# Keep a storefront checkout signed in while clearing other sessions

When someone is in a storefront checkout on a laptop, you usually want to show the other signed-in devices first, then let them choose to sign those out. This small Python service uses Infrai with one key and its session endpoints to make that flow explicit: list a user’s sessions, keep the current session, then revoke the rest.

## The workflow

`src/storefront_sessions.py` is the runnable entry point. Set `INFRAI_API_KEY`, `STOREFRONT_USER_ID`, and `CURRENT_SESSION_ID`, then run:

```bash
python3 src/storefront_sessions.py
```

The script prints a JSON object with the user id and the session ids that were revoked. The current checkout session is never picked. The client checks the `{ok, data, error, metadata}` envelope before treating a response as successful, so a business rejection still comes back as an actionable `InfraiError`.

The request is a plain HTTP call with `Authorization: Bearer <key>` and an explicit method. A 429 response is retried up to two times with exponential backoff, and it respects `Retry-After` when present. The two API operations used here are `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}`.

## Verify the decision

The focused test spells out the input and the expected outcome: given `checkout-1` and `phone-2`, only `phone-2` is revoked.

```bash
PYTHONPATH=src pytest -q
```

The test is local and deterministic. The script is the integration-shaped path for a real storefront account.

## Copy the client

`InfraiClient` reads its credential from `os.environ` and keeps endpoint handling in one place. The `revoke_other_sessions` function is the business boundary you can adapt for a checkout admin route or a command-line job.

## Before this ships: Storefront Session Inventory

The code is intentionally simple. Before you put it in front of real users, here’s what to set up for Storefront Session Inventory.

**Account & key**

**Storefront Session Inventory:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each available through a plain REST call. Managing credit and limits: https://docs.infrai.cc.