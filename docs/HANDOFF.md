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
- GitHub main commit: `807d50174246ff37784a653656d79c1965bab469`
- GitHub Actions: run `33946244639` passed compile, 6 unit tests, and demo smoke.
- Next issues: #3 persistent state/outbox/recovery; #9 real data/vintage adapters.

## Do not infer

Do not infer a live or profitable strategy from the demo. Do not call the ETF expression a pure curve spread. Do not claim real market data, replay correctness, or NautilusTrader support until those tests are actually run.
