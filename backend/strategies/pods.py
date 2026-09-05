from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.domain.models import DataSnapshot, DecisionStatus
from backend.strategies.curve_rv import curve_signal


@dataclass(frozen=True)
class PodResult:
    pod_id: str
    status: str
    as_of: datetime
    outputs: dict[str, Any]
    evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "pod_id": self.pod_id,
            "status": self.status,
            "as_of": self.as_of.isoformat(),
            "outputs": self.outputs,
            "evidence_ids": list(self.evidence_ids),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
        }


def _abstain(pod_id: str, snapshot: DataSnapshot, missing: list[str]) -> PodResult:
    return PodResult(pod_id, "ABSTAIN", snapshot.as_of, {"missing": missing}, warnings=("required_input_missing",))


def curve_rv_pod(snapshot: DataSnapshot, history: list[Decimal]) -> PodResult:
    signal = curve_signal(snapshot, history)
    status = "SIGNAL" if signal.status == DecisionStatus.APPROVED else signal.status.value
    return PodResult("curve_rv", status, snapshot.as_of, signal.model_dump(mode="json"), evidence_ids=(snapshot.snapshot_id,), assumptions=("rolling mean/stdev use only prior observations",))


def carry_roll_pod(snapshot: DataSnapshot) -> PodResult:
    required = ["carry_2y_bp", "roll_2y_12m_bp"]
    missing = [key for key in required if key not in snapshot.records]
    if missing:
        return _abstain("carry_roll", snapshot, missing)
    carry = snapshot.records["carry_2y_bp"]
    roll = snapshot.records["roll_2y_12m_bp"]
    return PodResult("carry_roll", "SIGNAL" if carry + roll > 0 else "NO_TRADE", snapshot.as_of, {"carry_bp": carry, "roll_bp": roll, "expected_total_bp": carry + roll}, evidence_ids=(snapshot.snapshot_id,), assumptions=("carry and roll are supplied by the curve model",))


def fed_path_pod(snapshot: DataSnapshot) -> PodResult:
    required = ["policy_rate", "front_end_rate"]
    missing = [key for key in required if key not in snapshot.records]
    if missing:
        return _abstain("fed_path", snapshot, missing)
    gap = snapshot.records["front_end_rate"] - snapshot.records["policy_rate"]
    scenario = "easing_bias" if gap < Decimal("-0.10") else "tightening_bias" if gap > Decimal("0.10") else "neutral"
    return PodResult("fed_path", "SCENARIO", snapshot.as_of, {"policy_rate": snapshot.records["policy_rate"], "front_end_rate": snapshot.records["front_end_rate"], "gap_bp": gap * 100, "scenario": scenario}, evidence_ids=(snapshot.snapshot_id,), assumptions=("front-end rate is a supplied research proxy, not a market-implied meeting probability",))


def inflation_pod(snapshot: DataSnapshot) -> PodResult:
    required = ["cpi_mom", "core_cpi_mom"]
    missing = [key for key in required if key not in snapshot.records]
    if missing:
        return _abstain("inflation", snapshot, missing)
    headline = snapshot.records["cpi_mom"]
    core = snapshot.records["core_cpi_mom"]
    return PodResult("inflation", "SIGNAL" if core > Decimal("0.003") else "NO_TRADE", snapshot.as_of, {"headline_mom": headline, "core_mom": core, "threshold": Decimal("0.003"), "bias": "inflationary" if core > Decimal("0.003") else "contained"}, evidence_ids=(snapshot.snapshot_id,), assumptions=("monthly rates are decimals, for example 0.003 = 0.3%",))


def macro_event_pod(snapshot: DataSnapshot) -> PodResult:
    if "event_surprise_bp" not in snapshot.records:
        return _abstain("macro_event", snapshot, ["event_surprise_bp"])
    surprise = snapshot.records["event_surprise_bp"]
    return PodResult("macro_event", "SIGNAL" if abs(surprise) >= Decimal("10") else "NO_TRADE", snapshot.as_of, {"surprise_bp": surprise, "window": "next_session", "direction": "rates_up" if surprise > 0 else "rates_down" if surprise < 0 else "none"}, evidence_ids=(snapshot.snapshot_id,), assumptions=("surprise must be measured against a timestamped consensus series",), warnings=("demo snapshot does not include a live consensus feed",))


def run_all_pods(snapshot: DataSnapshot, history: list[Decimal]) -> list[PodResult]:
    """Run all five pods; optional inputs abstain explicitly."""
    return [curve_rv_pod(snapshot, history), carry_roll_pod(snapshot), fed_path_pod(snapshot), inflation_pod(snapshot), macro_event_pod(snapshot)]
