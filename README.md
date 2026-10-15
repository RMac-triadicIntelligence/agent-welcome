# agent-welcome

A signed "agents may shop here" manifest for merchants, plus user-signed delegation receipts for agents.

Built on the "nothing may vouch for itself" principle: the agent proposes, the user authorizes, and the merchant's own verifier decides.

- `spec/`: `SPEC.md`, `agent-welcome.schema.json`, `delegation-receipt.schema.json`
- `agent_welcome/`: `core.py` (canonical JSON, Ed25519, cart digest), `verifier.py` (own clock, pinned keys, hash-chained spent-nonce log), `cli.py`
- `samples/`: welcoming, refusing, and tampered merchant manifests, built from fixed public demo seeds by `make_samples.py`
- `battery/`: preregistered `ACCEPTANCE.md` and its hash, `run.py`, `results/results.json`, and `RECEIPT.md`

## Run
```
pip install cryptography
python3 battery/run.py          # expects OVERALL: PASS
python3 -m agent_welcome.cli --help
sha256sum -c SHA256SUMS
```

## What the battery shows (15/15)
The valid purchase is accepted. Every other case is refused, fail closed, with a named reason:

- backdated expiry, replayed nonce, swapped cart
- tampered manifest, and a manifest fully resealed with another key
- agent outside the allowed list, price over the receipt cap, order over the merchant's maximum
- missing timestamp, future timestamp
- refusing merchant, receipt signed by the agent itself, blanked state head, receipt for another merchant

A crash is scored as a FAIL, never as a refusal.

## Honest limits
- **Draft.** Not audited and not production code. Not affiliated with Amazon, Shopify, Google, OpenAI, Stripe, or xAI.
- **Injected clock.** The battery gives the verifier a fixed clock. It never trusts a time supplied by the receipt, but in production you must use the real system clock, and the box's clock is only as trustworthy as its host.
- **Local state.** The nonce log and its head live in a local file. A blanked or edited head is caught, but an attacker who can rewrite the whole file, list and head together, or roll it back to an older consistent copy is not. That needs an outside witness, such as an append-only log or anchoring.
- **Key pinning.** It is assumed and not solved. How a merchant's key and a user's key get pinned (DNS, registry, account enrollment) is out of scope.
- **No real checkout.** No payments, revocation, or JSON Schema validation at runtime (the verifier checks fields in code). No concurrency control on the nonce log.
- **Demo keys.** The seeds in `samples/` are public. Never use them for real.
- **Relationship to other standards.** Meant to sit beside ACP, UCP, and AP2, not to replace them. It does not, and must not, be used to get around any site's agent restrictions.

License: Apache-2.0. See NOTICE.
