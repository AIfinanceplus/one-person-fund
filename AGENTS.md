# Agent instructions

## Scope

Build a rates-focused paper fund. Live trading, withdrawals, external investor reporting, and automatic public deployment are out of scope.

## Invariants

1. A proposal cannot bypass the deterministic risk and policy gates.
2. Raw data is append-only and every decision references a snapshot.
3. Duplicate order or fill events must not duplicate side effects.
4. Missing, stale, invalid, or ambiguous inputs cause `ABSTAIN`/`REJECTED`, never an invented value.
5. Demo, replay, and paper accounts stay separate.
6. Store rates as decimals internally (`0.0425` = 4.25%); store basis points explicitly.
7. Every status report distinguishes passed, failed, and not-run checks.

## Working style

Read `docs/STATUS.md`, `docs/HANDOFF.md`, and `docs/PROJECT_SPEC.md` before making changes. Keep the standard-library demo runnable. Add a focused test for each new accounting, risk, idempotency, or time-availability rule.
