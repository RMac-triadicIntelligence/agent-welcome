"""Merchant-side verifier. It owns its clock, its pinned keys, and its spent-nonce log.
Nothing in the manifest or receipt can supply 'now', trust, or state."""
import json, os
from .core import (SPEC, RECEIPT_SPEC, CLOCK_SKEW_S, MAX_RECEIPT_LIFETIME_S, canon, sha256_hex,
                   sig_ok, cart_digest, cart_total, SystemClock)

GENESIS = "0" * 64


class Refuse(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def chain_head(nonces):
    h = GENESIS
    for n in nonces:
        h = sha256_hex((h + n).encode())
    return h


class NonceLog:
    """Append-only spent-nonce log at `path`: {"nonces":[...], "head": hex}. The head must
    recompute from the list; a blanked or edited head refuses all verification."""
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            self._write([])

    def _write(self, nonces):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"nonces": nonces, "head": chain_head(nonces)}, f, sort_keys=True)
        os.replace(tmp, self.path)

    def load(self):
        with open(self.path) as f:
            st = json.load(f)
        nonces = st.get("nonces")
        if not isinstance(nonces, list) or st.get("head") != chain_head(nonces):
            raise Refuse("state_head_mismatch")
        return nonces

    def spend(self, nonce):
        nonces = self.load()
        if nonce in nonces:
            raise Refuse("nonce_replayed")
        nonces.append(nonce)
        self._write(nonces)
        return chain_head(nonces)


class Verifier:
    def __init__(self, merchant_id, pinned_merchant_keys, pinned_user_keys, state_path, clock=None):
        self.merchant_id = merchant_id
        self.pinned_merchant_keys = set(pinned_merchant_keys)
        self.pinned_user_keys = dict(pinned_user_keys)  # user_id -> pubkey hex
        self.log = NonceLog(state_path)
        self.clock = clock or SystemClock()

    def check_manifest(self, env):
        if not isinstance(env, dict) or "body" not in env:
            raise Refuse("manifest_malformed")
        if not sig_ok(env):
            raise Refuse("manifest_bad_signature")
        if env["key"] not in self.pinned_merchant_keys:
            raise Refuse("manifest_key_not_pinned")
        m = env["body"]
        if m.get("spec") != SPEC or m.get("merchant") != self.merchant_id:
            raise Refuse("manifest_malformed")
        if not m.get("agents_welcome"):
            raise Refuse("merchant_refuses")
        return m

    def verify(self, manifest_env, receipt_env, cart, agent_id):
        """Returns (decision, reason, head). Never raises on bad input."""
        try:
            m = self.check_manifest(manifest_env)
            if agent_id not in m.get("agents_allowed", []):
                raise Refuse("agent_not_allowed")
            if "buy" not in m.get("actions", []):
                raise Refuse("action_not_allowed")
            if not isinstance(receipt_env, dict) or "body" not in receipt_env:
                raise Refuse("receipt_malformed")
            r = receipt_env["body"]
            if r.get("spec") != RECEIPT_SPEC:
                raise Refuse("receipt_malformed")
            user_key = self.pinned_user_keys.get(r.get("user"))
            if not sig_ok(receipt_env) or receipt_env["key"] != user_key:
                raise Refuse("receipt_bad_signature")
            if r.get("merchant") != self.merchant_id:
                raise Refuse("wrong_merchant")
            if r.get("agent") != agent_id:
                raise Refuse("agent_mismatch")
            issued, expires = r.get("issued_at"), r.get("expires_at")
            if not isinstance(issued, int) or not isinstance(expires, int):
                raise Refuse("missing_timestamp")
            now = self.clock.now()  # verifier's own clock, never the receipt's
            if issued > now + CLOCK_SKEW_S:
                raise Refuse("future_timestamp")
            if expires <= now:
                raise Refuse("expired")
            if expires - issued > MAX_RECEIPT_LIFETIME_S or expires <= issued:
                raise Refuse("lifetime_invalid")
            if cart_digest(cart) != r.get("cart_digest"):
                raise Refuse("cart_mismatch")
            total = cart_total(cart)
            if total > int(r.get("price_cap_cents", -1)):
                raise Refuse("over_price_cap")
            if total > int(m.get("max_order_cents", -1)):
                raise Refuse("over_merchant_cap")
            nonce = r.get("nonce")
            if not isinstance(nonce, str) or len(nonce) < 16:
                raise Refuse("receipt_malformed")
            head = self.log.spend(nonce)
            return ("ACCEPT", "ok", head)
        except Refuse as e:
            return ("REFUSE", e.reason, None)
        except Exception as e:  # a crash is reported as a crash, never as a refusal
            return ("CRASH", type(e).__name__, None)
