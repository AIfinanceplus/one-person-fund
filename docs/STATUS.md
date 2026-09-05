# Status

## M0–M2 vertical slice — in progress

### Completed in this workspace

- Repository specification, agent instructions, Python package layout, role registry, domain objects, risk engine, paper broker, ledger, deterministic Curve RV demo, standard-library API, static command-center UI, and focused tests were created.
- The vertical slice is committed to `AIfinanceplus/one-person-fund` on `main`; the latest commit is the plan document commit recorded below.

### Verification

- Passed locally: `python -m backend.cli demo` returned `SUCCEEDED` with two fills and two ledger entries; `python -m unittest discover -s tests -v` ran 6 tests successfully; `python -m compileall -q backend tests`; API smoke returned `demo-run-001 SUCCEEDED 2` and 14 roles.
- Passed from a fresh GitHub checkout: compile, 6 unit tests, and `demo-run-001 SUCCEEDED 2 2`.
- Passed on GitHub Actions: final run `33946117324` succeeded for compile, unit tests, and demo smoke test.
- Not run: GitHub Actions, real data ingestion, REPLAY, PAPER forward observation, NautilusTrader integration, FastAPI/React build.

### Known limitations

- Demo data is a deterministic fixture.
- Paper execution uses two ETF legs with configurable fixed cost and simplified prices.
- No database persistence or multi-process worker exists yet; in-memory state demonstrates the domain invariants.
- API uses Python standard-library HTTP server for this vertical slice.

### Next

1. Begin GitHub issue #3: persistent task/event storage and recovery.
2. Begin GitHub issue #9: real data and vintage adapters.
3. Keep the first forward PAPER observation blocked until the M3 data and persistence gates pass.

### GitHub evidence

- Latest main commit: `807d50174246ff37784a653656d79c1965bab469`
- CI run: <https://github.com/AIfinanceplus/one-person-fund/actions/runs/33946244639>
- Issue backlog: #1–#14 in the repository
