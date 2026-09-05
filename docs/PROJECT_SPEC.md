# Project specification

## Product

One Person Fund is a rates-focused, paper-only Fund OS. The system demonstrates a complete, auditable event path from a data snapshot to research, quant validation, red-team challenge, portfolio proposal, deterministic risk decision, paper fill, reconciliation, and evaluation.

## Roles

The canonical role registry is `backend/contracts/roles.py`. It contains 14 roles: Chief of Staff, Data Steward, Macro Analyst, Inflation Analyst, Fed Analyst, Rates Strategist, Quant Researcher, Red Team, Portfolio Manager, Risk Manager, Execution Trader, Operations, Compliance, and Auditor/Evaluator.

## Strategy scope

Five pods are required: Curve RV, Carry & Roll, Fed Path, Inflation, and Macro Event. The first executable demo is a simplified ETF expression of a curve signal. It is not a pure DV01-neutral 2s10s trade. The remaining pods remain research-only until their data, tests, costs, and risk expression are explicitly accepted.

## Modes

- `DEMO`: fixed fixtures; proves engineering and failure paths.
- `REPLAY`: timestamped historical snapshots; proves time eligibility and replay.
- `PAPER`: forward market data with virtual execution; proves operational continuity.

No mode can route to a live broker.

## Non-negotiable invariants

- Risk and policy are deterministic and independent of the LLM explanation.
- Raw data is append-only, and every artifact has an input snapshot and version.
- Duplicate client order IDs and fill IDs are idempotent.
- Missing, stale, or invalid input yields explicit abstention or rejection.
- Orders carry proposal, risk, policy, mode, and expiry references.
- Ledger projections are rebuildable from event entries.

## Persistence milestone

`backend/state/store.py` is the first durable control-plane implementation. It uses SQLite with a run table, lease-based task claims, an append-only event table, and immutable artifact inserts. Its idempotency boundaries are event ID, task ID, and artifact ID. The persistent demo is still DEMO mode; it does not imply that market data or live execution is connected.

## Acceptance

The first acceptance target is one repeatable DEMO run with two fills, ledger entries, a visible API response, and tests for role coverage, risk rejection, order idempotency, and ledger idempotency. The M3 persistence slice adds a restart/reclaim test and two ordered durable events. Later milestones add real data, replay, and forward paper observation.
