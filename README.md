# One Person Fund — Rates Fund OS

Rates Fund OS is a paper-trading research and control system for a one-person, rates-focused fund. The first implementation is deliberately small: it proves the decision chain, deterministic risk gates, idempotent paper execution, an independent ledger, and a visible run state before any live integration.

## Current milestone

**M0–M2 vertical slice**

- 14 stable roles registered as machine-readable contracts.
- Five rates strategy pods registered; Curve RV is the first executable candidate.
- DEMO mode with deterministic curve data and a repeatable end-to-end run.
- `RiskEngine` performs code-based limits and rejects stale/invalid proposals.
- `PaperBroker` is idempotent and supports fills, cancellation, and restart-safe state.
- `Ledger` rebuilds positions, cash, NAV and P&L from events.
- Static command-center UI shows the pipeline and latest run artifacts.

This repository contains no live broker adapter and never submits live orders. `DEMO`, `REPLAY`, and `PAPER` are separate modes; the current demo uses fixed fixtures.

## Quick start

```bash
python -m backend.cli demo
python -m unittest discover -s tests -v
python -m backend.api
```

Open <http://127.0.0.1:8000> after starting the API server. The API server uses only the Python standard library in this milestone.

## Directory map

```text
backend/
  contracts/      role and task contracts
  domain/         typed fund objects and units
  execution/      paper execution port
  ledger/         event-sourced accounting
  orchestration/  deterministic demo workflow
  risk/           policy engine
  strategies/     rates strategy pods
frontend/         static command center
docs/             project specification, status and handoff
tests/            meaningful invariants and failure cases
```

## Safety boundaries

The model may propose a trade, but only deterministic policy code can authorize quantity and execution. Missing data, invalid units, stale metadata, expired approvals, and risk breaches return an explicit rejection or abstention. They are not filled with zeroes or fabricated values.

The demo uses a simplified ETF expression for Curve RV. It must not be described as a pure 2s10s DV01-neutral trade. The yield curve is a research input; ETF prices are a separate execution input.

## Development workflow

Use the milestones and acceptance gates in `docs/PROJECT_SPEC.md`. Update `docs/STATUS.md` and `docs/HANDOFF.md` at the end of every milestone with actual commands and results. Do not claim a market-data or live integration has been tested until the corresponding evidence is recorded.
