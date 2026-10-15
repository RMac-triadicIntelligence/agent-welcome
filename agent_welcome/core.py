import hashlib, json, time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

SPEC = "agent-welcome/0.1"
RECEIPT_SPEC = "agent-delegation-receipt/0.1"
CLOCK_SKEW_S = 60
MAX_RECEIPT_LIFETIME_S = 3600


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def key_from_seed(seed32: bytes):
    return Ed25519PrivateKey.from_private_bytes(seed32)


def pub_hex(priv):
    return priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def sign(priv, body):
    return {"body": body, "key": pub_hex(priv), "sig": priv.sign(canon(body)).hex()}


def sig_ok(env):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(env["key"])).verify(bytes.fromhex(env["sig"]), canon(env["body"]))
        return True
    except (InvalidSignature, ValueError, KeyError, TypeError):
        return False


def cart_digest(cart):
    """Cart = {"items":[{"sku","qty","unit_cents"}], "currency"}. Digest over canonical JSON."""
    return sha256_hex(canon(cart))


def cart_total(cart):
    return sum(int(i["qty"]) * int(i["unit_cents"]) for i in cart["items"])


class SystemClock:
    def now(self):
        return int(time.time())
