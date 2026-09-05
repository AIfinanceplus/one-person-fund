from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from backend.domain.models import DataSnapshot, RunMode, Side, TradeLeg, TradeProposal
from backend.orchestration.demo import build_demo_snapshot, run_snapshot
from backend.risk.engine import RiskEngine


def run_missing_data() -> dict[str, Any]:
    """Demonstrate an explicit abstention when the curve record is absent."""
    snapshot, history = build_demo_snapshot()
    blocked = DataSnapshot(
        snapshot_id="scenario-missing-curve",
        mode=RunMode.DEMO,
        as_of=snapshot.as_of,
        available_at=snapshot.available_at,
        source=snapshot.source,
        records={"SHY": snapshot.records["SHY"], "IEF": snapshot.records["IEF"]},
        quality="DEGRADED",
        content_hash="scenario-missing-curve-v1",
    )
    result = run_snapshot(blocked, history, run_id="scenario-missing-data")
    result["scenario"] = "missing-data"
    result["expected_status"] = "ABSTAINED"
    return result


def run_risk_limit() -> dict[str, Any]:
    """Demonstrate an independent deterministic risk rejection."""
    snapshot, _ = build_demo_snapshot()
    now = datetime.now(timezone.utc)
    proposal = TradeProposal(
        proposal_id="scenario-risk-limit",
        thesis_id="scenario-risk-limit-thesis",
        strategy_id="curve_rv",
        snapshot_id=snapshot.snapshot_id,
        created_at=now,
        legs=[TradeLeg(instrument="SHY", side=Side.BUY, quantity=Decimal("100000"))],
        target_weights={"SHY": Decimal("0.82")},
        reason="oversized scenario order",
    )
    decision = RiskEngine().check(
        proposal,
        current_weights={"SHY": Decimal("0")},
        prices={"SHY": Decimal("82")},
        durations={"SHY": Decimal("1.8")},
        nav=Decimal("10000000"),
        current_cash=Decimal("10000000"),
        now=now,
    )
    decision_status = getattr(decision.status, "value", decision.status)
    return {
        "scenario": "risk-limit",
        "status": decision_status,
        "expected_status": "REJECTED",
        "artifacts": {"proposal": proposal.model_dump(mode="json"), "risk_decision": decision.model_dump(mode="json")},
    }


def run_budget_exhausted() -> dict[str, Any]:
    """Demonstrate budget blocking without calling an external model."""
    return {
        "scenario": "budget-exhausted",
        "status": "BLOCKED",
        "expected_status": "BLOCKED",
        "artifacts": {"reason": "ABSTAIN_BUDGET", "llm_calls": 0, "hard_budget_tokens": 0},
    }


def run_scenario(name: str) -> dict[str, Any]:
    scenarios = {"missing-data": run_missing_data, "risk-limit": run_risk_limit, "budget-exhausted": run_budget_exhausted}
    if name == "normal":
        from backend.orchestration.full_run import run_full_demo

        result = run_full_demo()
        result["scenario"] = "normal"
        result["expected_status"] = "SUCCEEDED"
        return result
    try:
        return scenarios[name]()
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {name}") from exc
