from __future__ import annotations

from decimal import Decimal
from typing import Any

from backend.compliance.policy import check_proposal
from backend.evaluation.fundbench import run_fundbench
from backend.orchestration.demo import build_demo_snapshot, run_demo
from backend.portfolio.manager import build_portfolio_proposal
from backend.risk.engine import RiskEngine
from backend.strategies.pods import run_all_pods


def run_full_demo() -> dict[str, Any]:
    snapshot, history = build_demo_snapshot()
    pods = run_all_pods(snapshot, history)
    portfolio = build_portfolio_proposal(snapshot, pods)
    result = run_demo()
    artifacts = result.setdefault("artifacts", {})
    artifacts["pods"] = [pod.as_dict() for pod in pods]
    artifacts["portfolio"] = portfolio.as_dict()
    if portfolio.proposal and "risk_decision" in artifacts:
        risk = RiskEngine().check(portfolio.proposal, {"SHY": Decimal("0.50"), "IEF": Decimal("0.50")}, {"SHY": Decimal("82"), "IEF": Decimal("95")}, {"SHY": Decimal("1.8"), "IEF": Decimal("7.2")}, Decimal("10000000"), current_cash=Decimal("1000"), now=snapshot.available_at)
        artifacts["compliance"] = check_proposal(portfolio.proposal, risk, snapshot.mode, now=snapshot.available_at).as_dict()
    # Evaluate the complete artifact graph, not a smaller second DEMO run.
    artifacts["fundbench"] = run_fundbench(lambda: result).as_dict()
    result["status"] = "SUCCEEDED" if result.get("status") == "SUCCEEDED" else result.get("status")
    return result
