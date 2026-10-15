"""Preregistered battery. Checks ACCEPTANCE.md hash first, reads expectations from it, runs all cases.
Deterministic: fixed demo seeds, fixed nonces, a fixed clock injected into the verifier (not the receipt)."""
import hashlib, json, os, re, sys, tempfile, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "samples"))
from agent_welcome.core import key_from_seed, sign, pub_hex, cart_digest, RECEIPT_SPEC
from agent_welcome.verifier import Verifier
import make_samples as S

def fail(msg):
    print("OVERALL: FAIL —", msg); sys.exit(1)

acc = open(os.path.join(HERE, "ACCEPTANCE.md"), "rb").read()
pinned = open(os.path.join(HERE, "ACCEPTANCE.sha256")).read().strip()
acc_hash = hashlib.sha256(acc).hexdigest()
if acc_hash != pinned:
    fail("ACCEPTANCE.md does not match its preregistered hash")
EXPECT = {m[0]: (m[1], m[2]) for m in re.findall(r"^\| (C\d\d) \|[^|]+\| (ACCEPT|REFUSE) \| (\w+) \|$", acc.decode(), re.M)}

class FixedClock:
    def __init__(self, t): self.t = t
    def now(self): return self.t

NOW = S.T0 + 1000
M = S.build()
PINS = json.load(open(os.path.join(HERE, "..", "samples", "PINNED_KEYS.json")))
USER = key_from_seed(S.seed("user:rusty"))
AGENT = key_from_seed(S.seed("agent:grok-bot"))
ROGUE = key_from_seed(S.seed("attacker"))
CART = {"currency": "USD", "items": [{"sku": "LEGO-10294", "qty": 1, "unit_cents": 17999}]}
SWAP = {"currency": "USD", "items": [{"sku": "LEGO-10294", "qty": 3, "unit_cents": 17999}]}
BIG = {"currency": "USD", "items": [{"sku": "TV-85", "qty": 1, "unit_cents": 90000}]}

def receipt(key=USER, merchant="welcoming.example", agent="grok-bot", cart=CART, cap=20000,
            issued=NOW - 60, expires=NOW + 600, nonce="n-0001-aaaaaaaaaaaa", drop=()):
    b = {"spec": RECEIPT_SPEC, "user": "rusty", "merchant": merchant, "agent": agent,
         "cart_digest": cart_digest(cart), "price_cap_cents": cap, "issued_at": issued,
         "expires_at": expires, "nonce": nonce}
    for d in drop: b.pop(d)
    return sign(key, b)

def verifier(state, merchant="welcoming.example", pin="welcoming"):
    return Verifier(merchant, [PINS[pin]], {"rusty": pub_hex(USER)}, state, clock=FixedClock(NOW))

def run_cases(tmp):
    out = {}
    def st(n): return os.path.join(tmp, n + ".json")
    shared = st("shared")
    v = verifier(shared)
    out["C01"] = v.verify(M["welcoming"], receipt(), CART, "grok-bot")
    out["C02"] = verifier(st("c02")).verify(M["welcoming"], receipt(issued=NOW - 7200, expires=NOW - 6900, nonce="n-0002-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C03"] = verifier(shared).verify(M["welcoming"], receipt(), CART, "grok-bot")
    out["C04"] = verifier(st("c04")).verify(M["welcoming"], receipt(nonce="n-0004-aaaaaaaaaaaa"), SWAP, "grok-bot")
    out["C05"] = verifier(st("c05"), "tampered.example", "tampered").verify(M["tampered"], receipt(merchant="tampered.example", nonce="n-0005-aaaaaaaaaaaa"), CART, "grok-bot")
    reseal_body = copy.deepcopy(M["welcoming"]["body"]); reseal_body["max_order_cents"] = 5000000
    out["C06"] = verifier(st("c06")).verify(sign(ROGUE, reseal_body), receipt(nonce="n-0006-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C07"] = verifier(st("c07")).verify(M["welcoming"], receipt(agent="shady-agent", nonce="n-0007-aaaaaaaaaaaa"), CART, "shady-agent")
    out["C08"] = verifier(st("c08")).verify(M["welcoming"], receipt(cap=10000, nonce="n-0008-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C09"] = verifier(st("c09")).verify(M["welcoming"], receipt(drop=("issued_at",), nonce="n-0009-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C10"] = verifier(st("c10")).verify(M["welcoming"], receipt(issued=NOW + 3000, expires=NOW + 3300, nonce="n-0010-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C11"] = verifier(st("c11"), "refusing.example", "refusing").verify(M["refusing"], receipt(merchant="refusing.example", nonce="n-0011-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C12"] = verifier(st("c12")).verify(M["welcoming"], receipt(key=AGENT, nonce="n-0012-aaaaaaaaaaaa"), CART, "grok-bot")
    s = json.load(open(shared)); s["head"] = ""; json.dump(s, open(shared, "w"))
    out["C13"] = verifier(shared).verify(M["welcoming"], receipt(), CART, "grok-bot")
    out["C14"] = verifier(st("c14")).verify(M["welcoming"], receipt(merchant="other.example", nonce="n-0014-aaaaaaaaaaaa"), CART, "grok-bot")
    out["C15"] = verifier(st("c15")).verify(M["welcoming"], receipt(cart=BIG, cap=100000, nonce="n-0015-aaaaaaaaaaaa"), BIG, "grok-bot")
    return out

with tempfile.TemporaryDirectory() as tmp:
    got = run_cases(tmp)

rows, ok_all = [], True
for cid in sorted(EXPECT):
    exp_d, exp_r = EXPECT[cid]
    d, r, head = got.get(cid, ("MISSING", "missing", None))
    passed = (d == exp_d and r == exp_r)  # CRASH never matches an expectation
    ok_all &= passed
    rows.append({"id": cid, "expected": [exp_d, exp_r], "got": [d, r], "head": head, "pass": passed})
if set(got) != set(EXPECT):
    ok_all = False

results = {"battery": "agent-welcome v1", "acceptance_sha256": acc_hash, "cases": rows,
           "overall": "PASS" if ok_all else "FAIL"}
blob = (json.dumps(results, indent=2, sort_keys=True) + "\n").encode()
outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, "results.json"), "wb").write(blob)
for r in rows:
    print(f"{r['id']} {'PASS' if r['pass'] else 'FAIL'}  expected {r['expected'][0]}/{r['expected'][1]}  got {r['got'][0]}/{r['got'][1]}")
print("results sha256:", hashlib.sha256(blob).hexdigest())
print("OVERALL:", results["overall"])
sys.exit(0 if ok_all else 1)
