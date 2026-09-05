# Status

## M0–M2 vertical slice — verified; M3 in progress

### Completed in this workspace

- Repository specification, agent instructions, Python package layout, role registry, domain objects, risk engine, paper broker, ledger, deterministic Curve RV demo, standard-library API, static command-center UI, and focused tests were created.
- The vertical slice is committed to `AIfinanceplus/one-person-fund` on `main`; the latest commit is the plan document commit recorded below.

### Verification

- Passed locally: `python -m backend.cli demo` returned `SUCCEEDED` with two fills and two ledger entries; `python -m unittest discover -s tests -v` ran 6 tests successfully; `python -m compileall -q backend tests`; API smoke returned `demo-run-001 SUCCEEDED 2` and 14 roles.
- Passed on GitHub Actions: final run `33946117324` succeeded for compile, unit tests, and demo smoke test.
- M3 passed locally and on GitHub: SQLite `StateStore`, fixture source, durable demo runner, and 8 tests pass.
- Not run: GitHub Actions, real data ingestion, REPLAY, PAPER forward observation, NautilusTrader integration, FastAPI/React build.

### Known limitations

- Demo data is a deterministic fixture.
- Paper execution uses two ETF legs with configurable fixed cost and simplified prices.
- No database persistence or multi-process worker exists yet; in-memory state demonstrates the domain invariants.
- API uses Python standard-library HTTP server for this vertical slice.

### Next

1. Review GitHub issue #3 against the M3 implementation.
2. Continue GitHub issue #9: real data and vintage adapters.
3. Keep the first forward PAPER observation blocked until the M3 data and persistence gates pass.

### GitHub evidence

- M3 implementation baseline: `428f37a529e550207b0079f4cdc540dc5ec43fed`
- CI run: <https://github.com/AIfinanceplus/one-person-fund/actions/runs/33946465641>
- Issue backlog: #1–#14 in the repository
