# agent-welcome 0.1 — draft spec

## Principle
Nothing may vouch for itself. The agent **proposes** a cart. The **user** authorizes it with a signed receipt. The **merchant's own verifier** decides, using its own clock, its own pinned keys, and its own spent-nonce log.

## 1. Manifest
- Served at `/.well-known/agent-welcome.json`. It is an envelope `{body, key, sig}`.
- The signature is Ed25519 over canonical JSON of `body`: sorted keys, `,` and `:` separators, UTF-8.
- Verifiers MUST pin the merchant key out of band, for example via DNS TXT, a registry, or prior visits. A manifest re-signed with any other key is refused (`manifest_key_not_pinned`).
- `agents_welcome: false` is a valid, signed refusal (`merchant_refuses`).
- Schema: `agent-welcome.schema.json`.

## 2. Delegation receipt
- Signed by the user's key, which the merchant holds pinned for the user's account.
- Bound to:
  - `merchant`
  - `agent`
  - `cart_digest`: SHA-256 of the canonical cart
  - `price_cap_cents`
  - `issued_at` and `expires_at`, in integer Unix seconds, with a lifetime of at most 3600 s
  - a single-use `nonce`
- Schema: `delegation-receipt.schema.json`.

## 3. Verification order (first failure wins, fail closed)
1. Manifest signature, then the pinned key, then spec and merchant, then `agents_welcome`.
2. The agent is in `agents_allowed`, and `buy` is in `actions`.
3. The receipt signature is valid AND made by the pinned user key. An agent signing for itself is refused.
4. The receipt names this merchant and this agent.
5. Timestamps are present and are integers. Then, by the verifier's clock: `issued_at` is no more than 60 s ahead, `expires_at` is after now, and the lifetime is valid.
6. The cart digest matches, the total is within the price cap, and the total is within the merchant's maximum order.
7. Nonce log: the stored head must recompute from the stored list, otherwise `state_head_mismatch`. Then the nonce must not have been spent before, otherwise `nonce_replayed`. Then it is appended, and the new head is returned.

Any exception is reported as `CRASH`, never as a refusal.

## Reason codes
`ok`, `manifest_malformed`, `manifest_bad_signature`, `manifest_key_not_pinned`, `merchant_refuses`, `agent_not_allowed`, `action_not_allowed`, `receipt_malformed`, `receipt_bad_signature`, `wrong_merchant`, `agent_mismatch`, `missing_timestamp`, `future_timestamp`, `expired`, `lifetime_invalid`, `cart_mismatch`, `over_price_cap`, `over_merchant_cap`, `state_head_mismatch`, `nonce_replayed`.
