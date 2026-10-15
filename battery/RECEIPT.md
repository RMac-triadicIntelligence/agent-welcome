# Battery receipt — agent-welcome v1
- Acceptance list: battery/ACCEPTANCE.md, sha256 `8d499872ccf226d117197bc907d4acb9b283c9ba58b2aee84cf63a6d4909bb5f` (hash recorded before the verifier was written)
- Result: **OVERALL: PASS**, 15/15 cases, each with the exact preregistered decision and reason.
- results.json sha256: `d5139a413e4288a84292487a70821aee8b61bd08567eb999232aa18aa2d83438`
- Two independent runs (2026-10-15, Python 3.13.5, cryptography 43.0.0) wrote byte-identical results.json.
- Disclosure: the first run failed C15 because of a harness bug. The receipt was built for the wrong cart, so the verifier correctly said cart_mismatch. Only the harness line was fixed. ACCEPTANCE.md and the verifier were not touched, and the hash still matches.
- Not externally witnessed. The timestamp becomes an outside record only once this is pushed to GitHub.
