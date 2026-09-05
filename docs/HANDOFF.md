# Handoff

## Current target

M3 persistence and time-aware fixture slice for Rates Fund OS.

## Resume sequence

```bash
python -m backend.cli demo
python -m backend.cli persistent-demo --db /tmp/rates-fund.sqlite3
python -m unittest discover -s tests -v
python -m backend.api
```

## Evidence required before calling this milestone verified

- The demo returns `SUCCEEDED`, exactly two fills, two ledger entries, and a deterministic risk decision.
- Unit tests cover role registry, risk rejection, duplicate order idempotency, and duplicate fill idempotency.
- The API exposes `/api/demo` and `/api/roles`; the UI reads the real demo response.
- M3 implementation baseline: `3a19fd7606742d3385fb966d11c01195b6b0a85a`
- GitHub Actions: run `33946589948` passed compile, 10 unit tests, demo smoke, and durable demo smoke.
- Next issues: #3 persistent state/outbox/recovery; #9 real data/vintage adapters.
- M3 local evidence: 10 unit tests pass; persistent demo returns `SUCCEEDED` with two durable events and a completed run; adapter tests use injected local XML/CSV.

## Do not infer

Do not infer a live or profitable strategy from the demo. Do not call the ETF expression a pure curve spread. Do not claim real market data, replay correctness, or NautilusTrader support until those tests are actually run. SQLite durability here is a control-plane slice, not a multi-process production deployment.
