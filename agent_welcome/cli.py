"""CLI: keygen | sign-manifest | issue-receipt | verify-manifest | verify"""
import argparse, json, os, sys, secrets, time
from .core import key_from_seed, pub_hex, sign, sig_ok, cart_digest, RECEIPT_SPEC
from .verifier import Verifier


def _load(p):
    with open(p) as f:
        return json.load(f)


def _key(p):
    return key_from_seed(bytes.fromhex(open(p).read().strip()))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="agent-welcome")
    sp = ap.add_subparsers(dest="cmd", required=True)
    k = sp.add_parser("keygen"); k.add_argument("out")
    s = sp.add_parser("sign-manifest"); s.add_argument("key"); s.add_argument("body"); s.add_argument("out")
    r = sp.add_parser("issue-receipt"); r.add_argument("user_key"); r.add_argument("--user", required=True)
    r.add_argument("--merchant", required=True); r.add_argument("--agent", required=True)
    r.add_argument("--cart", required=True); r.add_argument("--cap-cents", type=int, required=True)
    r.add_argument("--ttl", type=int, default=900); r.add_argument("out")
    vm = sp.add_parser("verify-manifest"); vm.add_argument("manifest"); vm.add_argument("--pin", action="append", required=True)
    v = sp.add_parser("verify"); v.add_argument("--merchant", required=True); v.add_argument("--manifest", required=True)
    v.add_argument("--receipt", required=True); v.add_argument("--cart", required=True); v.add_argument("--agent", required=True)
    v.add_argument("--pin", action="append", required=True); v.add_argument("--user-pin", action="append", required=True, help="user_id=pubhex")
    v.add_argument("--state", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "keygen":
        fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, secrets.token_bytes(32).hex().encode()); os.close(fd)
        print(pub_hex(_key(a.out)))
    elif a.cmd == "sign-manifest":
        json.dump(sign(_key(a.key), _load(a.body)), open(a.out, "w"), indent=2, sort_keys=True)
    elif a.cmd == "issue-receipt":
        now = int(time.time())
        body = {"spec": RECEIPT_SPEC, "user": a.user, "merchant": a.merchant, "agent": a.agent,
                "cart_digest": cart_digest(_load(a.cart)), "price_cap_cents": a.cap_cents,
                "issued_at": now, "expires_at": now + a.ttl, "nonce": secrets.token_hex(16)}
        json.dump(sign(_key(a.user_key), body), open(a.out, "w"), indent=2, sort_keys=True)
    elif a.cmd == "verify-manifest":
        env = _load(a.manifest)
        ok = sig_ok(env) and env["key"] in a.pin
        print("OK" if ok else "REFUSE"); return 0 if ok else 1
    elif a.cmd == "verify":
        users = dict(x.split("=", 1) for x in a.user_pin)
        v = Verifier(a.merchant, a.pin, users, a.state)
        d, reason, head = v.verify(_load(a.manifest), _load(a.receipt), _load(a.cart), a.agent)
        print(json.dumps({"decision": d, "reason": reason, "head": head}))
        return 0 if d == "ACCEPT" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
