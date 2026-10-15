# agent-welcome battery v1 — preregistered acceptance list
Written before the verifier code. Its SHA-256 is recorded in ACCEPTANCE.sha256 and checked by run.py before any case runs.

Rules:
- Each case must end with the stated decision AND the stated reason code.
- A crash, exception, or any other reason is a FAIL, never a refusal.
- The verifier uses its own clock and its own spent-nonce log with a hash-chained head. The receipt and manifest cannot supply "now", trusted keys, or state.
- Two full runs must produce byte-identical results.json.

| id | case | expected | reason |
|---|---|---|---|
| C01 | valid path: welcoming merchant, allowed agent, cart matches, under cap, fresh | ACCEPT | ok |
| C02 | backdated expiry: issued and expired in the past (claims a stale "now") | REFUSE | expired |
| C03 | replay: the C01 receipt presented a second time | REFUSE | nonce_replayed |
| C04 | cart swap: receipt is valid, but the presented cart differs | REFUSE | cart_mismatch |
| C05 | tampered manifest: body edited, original signature kept | REFUSE | manifest_bad_signature |
| C06 | fully resealed tamper: body edited and re-signed with a non-pinned key | REFUSE | manifest_key_not_pinned |
| C07 | agent outside the manifest's allowed agents | REFUSE | agent_not_allowed |
| C08 | cart total over the receipt price cap | REFUSE | over_price_cap |
| C09 | missing timestamp (issued_at absent) | REFUSE | missing_timestamp |
| C10 | issued_at in the future beyond skew | REFUSE | future_timestamp |
| C11 | refusing merchant (manifest says agents not welcome) | REFUSE | merchant_refuses |
| C12 | self-vouched receipt: signed by the agent's own key, not the user's | REFUSE | receipt_bad_signature |
| C13 | emptied state head: the spent-nonce log's stored head is blanked, then C01 is replayed | REFUSE | state_head_mismatch |
| C14 | the receipt is for a different merchant | REFUSE | wrong_merchant |
| C15 | cart over the merchant's manifest max order | REFUSE | over_merchant_cap |
