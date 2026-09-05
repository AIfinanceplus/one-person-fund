# Status

## M0–M2 vertical slice — in progress

### Completed in this workspace

- Repository specification, agent instructions, Python package layout, role registry, domain objects, risk engine, paper broker, ledger, deterministic Curve RV demo, standard-library API, static command-center UI, and focused tests were created.
- The first vertical slice is ready to commit to `AIfinanceplus/one-person-fund`.

### Verification

- Passed locally: `python -m backend.cli demo` returned `SUCCEEDED` with two fills and two ledger entries; `python -m unittest discover -s tests -v` ran 6 tests successfully; `python -m compileall -q backend tests`; API smoke returned `demo-run-001 SUCCEEDED 2` and 14 roles.
- Not run: GitHub Actions, real data ingestion, REPLAY, PAPER forward observation, NautilusTrader integration, FastAPI/React build.

### Known limitations

- Demo data is a deterministic fixture.
- Paper execution uses two ETF legs with configurable fixed cost and simplified prices.
- No database persistence or multi-process worker exists yet; in-memory state demonstrates the domain invariants.
- API uses Python standard-library HTTP server for this vertical slice.

### Next

1. Commit the M0–M2 vertical slice to `AIfinanceplus/one-person-fund`.
2. Run the same tests from the GitHub checkout and add CI.
3. Add persistent task/event storage and a real data adapter as M3.
