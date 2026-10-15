"""Builds the three sample merchants from FIXED, PUBLIC demo seeds. Never use these keys for real."""
import json, os, sys, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent_welcome.core import key_from_seed, sign, pub_hex

def seed(label): return hashlib.sha256(("agent-welcome-demo:" + label).encode()).digest()
D = os.path.dirname(os.path.abspath(__file__))
T0 = 1792000000

def body(merchant, welcome):
    return {"spec": "agent-welcome/0.1", "merchant": merchant, "agents_welcome": welcome,
            "agents_allowed": ["grok-bot", "example-agent"] if welcome else [],
            "actions": ["browse", "cart", "buy", "return"] if welcome else [],
            "max_order_cents": 50000, "currency": "USD", "require_agent_id": True,
            "require_delegation_receipt": True, "terms_url": "https://example.test/agent-terms",
            "protocols": ["agent-welcome/0.1"], "issued_at": T0}

def build():
    out = {}
    out["welcoming"] = sign(key_from_seed(seed("merchant:welcoming")), body("welcoming.example", True))
    out["refusing"] = sign(key_from_seed(seed("merchant:refusing")), body("refusing.example", False))
    t = sign(key_from_seed(seed("merchant:tampered")), body("tampered.example", True))
    t["body"]["max_order_cents"] = 5000000  # edited after signing; original signature kept
    out["tampered"] = t
    return out

if __name__ == "__main__":
    for name, env in build().items():
        with open(os.path.join(D, f"{name}.agent-welcome.json"), "w") as f:
            json.dump(env, f, indent=2, sort_keys=True); f.write("\n")
    pins = {n: pub_hex(key_from_seed(seed(f"merchant:{n}"))) for n in ("welcoming", "refusing", "tampered")}
    with open(os.path.join(D, "PINNED_KEYS.json"), "w") as f:
        json.dump(pins, f, indent=2, sort_keys=True); f.write("\n")
