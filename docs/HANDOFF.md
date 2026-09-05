# Handoff

## Current target

M0–M2 vertical slice for Rates Fund OS.

## Resume sequence

```bash
python -m backend.cli demo
python -m unittest discover -s tests -v
python -m backend.api
```

## Evidence required before calling this milestone verified

- The demo returns `SUCCEEDED`, exactly two fills, two ledger entries, and a deterministic risk decision.
- Unit tests cover role registry, risk rejection, duplicate order idempotency, and duplicate fill idempotency.
- The API exposes `/api/demo` and `/api/roles`; the UI reads the real demo response.
- GitHub commit SHA and any CI result are recorded here after the initial commit.

## Do not infer

Do not infer a live or profitable strategy from the demo. Do not call the ETF expression a pure curve spread. Do not claim real market data, replay correctness, or NautilusTrader support until those tests are actually run.
