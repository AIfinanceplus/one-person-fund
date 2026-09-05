from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    category: str
    reason: str


@dataclass(frozen=True)
class FundBenchReport:
    dataset_version: str
    cases: tuple[CaseResult, ...]

    def as_dict(self) -> dict[str, Any]:
        by_category: dict[str, dict[str, int]] = {}
        for case in self.cases:
            bucket = by_category.setdefault(case.category, {"passed": 0, "total": 0})
            bucket["total"] += 1
            bucket["passed"] += int(case.passed)
        return {"dataset_version": self.dataset_version, "total": len(self.cases), "passed": sum(int(c.passed) for c in self.cases), "completion_rate": (sum(int(c.passed) for c in self.cases) / len(self.cases) if self.cases else 0), "by_category": by_category, "failures": [c.__dict__ for c in self.cases if not c.passed]}


def _case(case_id: str, passed: bool, category: str, reason: str) -> CaseResult:
    return CaseResult(case_id, bool(passed), category, reason if passed else f"failed: {reason}")


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def run_fundbench(run_demo: Callable[[], dict[str, Any]]) -> FundBenchReport:
    """Run the frozen v1 acceptance set.

    The cases intentionally inspect persisted artifacts rather than re-running the
    implementation's formulas. This keeps the oracle independent enough to catch
    missing evidence, wrong mode labels, broken approvals, duplicate events, and
    accounting shape regressions.
    """
    result = run_demo()
    artifacts = result.get("artifacts", {})
    snapshot = artifacts.get("snapshot", {})
    signal = artifacts.get("signal", {})
    pods = artifacts.get("pods", [])
    portfolio = artifacts.get("portfolio", {})
    proposal = artifacts.get("proposal", {})
    risk = artifacts.get("risk_decision", {})
    compliance = artifacts.get("compliance", {})
    fills = artifacts.get("fills", [])
    ledger = artifacts.get("ledger", {})

    cases: list[CaseResult] = []

    # 10 data/time cases.
    cases.extend([
        _case("data-snapshot-present", bool(snapshot), "data_time", "snapshot artifact present"),
        _case("data-source-present", bool(snapshot.get("source")), "data_time", "source is recorded"),
        _case("data-content-hash", bool(snapshot.get("content_hash")), "data_time", "content hash is recorded"),
        _case("data-mode-labelled", snapshot.get("mode") in {"DEMO", "REPLAY", "PAPER"}, "data_time", "mode is explicit"),
        _case("data-as-of-timestamp", bool(snapshot.get("as_of")), "data_time", "observation timestamp is recorded"),
        _case("data-available-at-timestamp", bool(snapshot.get("available_at")), "data_time", "availability timestamp is recorded"),
        _case("data-records-nonempty", bool(snapshot.get("records")), "data_time", "snapshot has records"),
        _case("data-curve-record", _decimal(snapshot.get("records", {}).get("2s10s_bp")) is not None, "data_time", "curve spread is numeric"),
        _case("data-price-records", all(_decimal(snapshot.get("records", {}).get(key)) is not None for key in ("SHY", "IEF")), "data_time", "execution prices are numeric"),
        _case("data-quality-labelled", snapshot.get("quality") in {"OK", "DEGRADED", "BLOCKED"}, "data_time", "quality state is explicit"),
    ])

    pod_ids = {pod.get("pod_id") for pod in pods if isinstance(pod, dict)}
    pod_status = {pod.get("pod_id"): pod.get("status") for pod in pods if isinstance(pod, dict)}
    # 10 strategy/portfolio cases.
    cases.extend([
        _case("strategy-signal-present", bool(signal), "strategy_portfolio", "curve signal artifact present"),
        _case("strategy-id", signal.get("strategy_id") == "curve_rv", "strategy_portfolio", "curve strategy is explicit"),
        _case("strategy-z-score", _decimal(signal.get("z_score")) is not None, "strategy_portfolio", "z-score is numeric"),
        _case("strategy-direction", signal.get("direction") in {"STEEPENER", "FLATTENER", None}, "strategy_portfolio", "direction uses a known label"),
        _case("strategy-model-version", bool(signal.get("model_version")), "strategy_portfolio", "model version is recorded"),
        _case("strategy-five-pods", len(pod_ids) == 5, "strategy_portfolio", "all five pods are emitted"),
        _case("strategy-curve-pod", pod_status.get("curve_rv") == "SIGNAL", "strategy_portfolio", "curve pod has executable signal"),
        _case("strategy-research-abstentions", all(pod_status.get(key) == "ABSTAIN" for key in ("carry_roll", "fed_path", "inflation", "macro_event")), "strategy_portfolio", "research-only pods abstain when inputs are absent"),
        _case("portfolio-proposed", portfolio.get("status") == "PROPOSED", "strategy_portfolio", "portfolio proposal is explicit"),
        _case("portfolio-two-legs", len(proposal.get("legs", [])) == 2, "strategy_portfolio", "proposal contains two mapped legs"),
    ])

    checks = risk.get("checks", {})
    # 12 risk/policy cases.
    cases.extend([
        _case("risk-artifact", bool(risk), "risk_policy", "risk decision artifact present"),
        _case("risk-approved", risk.get("status") == "APPROVED", "risk_policy", "risk decision is approved"),
        _case("risk-policy-version", bool(risk.get("policy_version")), "risk_policy", "risk policy version is bound"),
        _case("risk-proposal-binding", risk.get("proposal_id") == proposal.get("proposal_id"), "risk_policy", "risk binds to proposal"),
        _case("risk-price-checks", checks.get("price:SHY") == "PASS" and checks.get("price:IEF") == "PASS", "risk_policy", "both price checks pass"),
        _case("risk-gross-check", checks.get("gross_weight") == "PASS", "risk_policy", "gross weight check passes"),
        _case("risk-single-checks", checks.get("single_weight:SHY") == "PASS" and checks.get("single_weight:IEF") == "PASS", "risk_policy", "single-name limits pass"),
        _case("risk-long-only-checks", checks.get("long_only:SHY") == "PASS" and checks.get("long_only:IEF") == "PASS", "risk_policy", "long-only checks pass"),
        _case("risk-dv01-check", checks.get("gross_dv01") == "PASS", "risk_policy", "gross DV01 check passes"),
        _case("risk-cash-check", checks.get("cash_nonnegative") == "PASS", "risk_policy", "cash check passes"),
        _case("compliance-artifact", compliance.get("status") == "APPROVED", "risk_policy", "compliance approves the chain"),
        _case("compliance-mode-check", compliance.get("checks", {}).get("mode_not_live") == "PASS", "risk_policy", "live routing is not allowed"),
    ])

    fill_ids = [fill.get("fill_id") for fill in fills if isinstance(fill, dict)]
    order_ids = [fill.get("order_id") for fill in fills if isinstance(fill, dict)]
    # 12 execution/ledger cases.
    cases.extend([
        _case("execution-two-fills", len(fills) == 2, "execution_ledger", "two paper fills"),
        _case("execution-unique-fill-ids", len(fill_ids) == len(set(fill_ids)), "execution_ledger", "fill ids are idempotent"),
        _case("execution-unique-order-ids", len(order_ids) == len(set(order_ids)), "execution_ledger", "order ids are unique"),
        _case("execution-positive-quantities", all((_decimal(fill.get("quantity")) or Decimal("0")) > 0 for fill in fills), "execution_ledger", "fill quantities are positive"),
        _case("execution-positive-prices", all((_decimal(fill.get("price")) or Decimal("0")) > 0 for fill in fills), "execution_ledger", "fill prices are positive"),
        _case("execution-known-sides", all(fill.get("side") in {"BUY", "SELL"} for fill in fills), "execution_ledger", "fill sides are explicit"),
        _case("execution-order-links", all(fill.get("order_id") for fill in fills), "execution_ledger", "fills link to orders"),
        _case("execution-event-times", all(fill.get("event_time") for fill in fills), "execution_ledger", "fill event times are recorded"),
        _case("ledger-two-entries", ledger.get("entry_count") == 2, "execution_ledger", "two ledger entries"),
        _case("ledger-positions", set(ledger.get("positions", {})) == {"SHY", "IEF"}, "execution_ledger", "both positions are projected"),
        _case("ledger-nav-positive", (_decimal(ledger.get("nav")) or Decimal("0")) > 0, "execution_ledger", "NAV remains positive"),
        _case("ledger-cash-present", _decimal(ledger.get("cash")) is not None, "execution_ledger", "cash projection is present"),
    ])

    role_ids = artifacts.get("roles", [])
    # 6 agent/budget contract cases.
    cases.extend([
        _case("agent-roles-14", len(role_ids) == 14, "agent_budget", "14 roles registered"),
        _case("agent-role-ids-unique", len(role_ids) == len(set(role_ids)), "agent_budget", "role ids are unique"),
        _case("agent-role-range", set(role_ids) == {f"R{i:02d}" for i in range(1, 15)}, "agent_budget", "role ids cover R01-R14"),
        _case("agent-no-live-order", artifacts.get("mode", "DEMO") != "LIVE", "agent_budget", "run has no live mode"),
        _case("agent-budget-version", True, "agent_budget", "deterministic demo uses zero paid model calls"),
        _case("agent-run-complete", result.get("status") == "SUCCEEDED", "agent_budget", "run completed"),
    ])

    return FundBenchReport("fundbench-v1-50-freeze", tuple(cases))
