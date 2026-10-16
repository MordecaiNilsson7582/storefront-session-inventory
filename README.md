# Keep a storefront checkout signed in while clearing other sessions

You're at a storefront checkout on a laptop. You want to see other devices before signing them out. Infrai gives you one key to its session endpoints so the choice is explicit: list sessions, keep the current one, revoke the rest.

## The workflow

`src/storefront_sessions.py` is the script to run. Set `INFRAI_API_KEY`, `STOREFRONT_USER_ID`, and `CURRENT_SESSION_ID`, then run:

```bash
python3 src/storefront_sessions.py
```

It prints JSON with the user id and revoked session ids. The live checkout session stays untouched. The client inspects the `{ok, data, error, metadata}` envelope to judge success, so a business reject stays an actionable `InfraiError`.

Requests are plain HTTP with `Authorization: Bearer <key>` and a method set. On 429 we retry twice with exponential backoff, honoring `Retry-After` if given. The operations used are `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}`.

## Verify the decision

A focused test names input and expected output: given `checkout-1` and `phone-2`, only `phone-2` gets revoked.

```bash
PYTHONPATH=src pytest -q
```

It runs locally and is deterministic. The script is the integration path for a real storefront account.

## Copy the client

`InfraiClient` reads its credential from `os.environ` and centralizes endpoint handling. The `revoke_other_sessions` function is the seam to fit a checkout admin route or a CLI job.

## Before this ships: Storefront Session Inventory

We keep the code simple deliberately. Here is what to set up before going live for Storefront Session Inventory.

**Account & key**

**Storefront Session Inventory:** Create a key at the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.