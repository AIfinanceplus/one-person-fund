from __future__ import annotations

from decimal import Decimal
from statistics import mean, pstdev

from backend.domain.models import CurveSignal, DataSnapshot, DecisionStatus


def curve_signal(snapshot: DataSnapshot, history: list[Decimal], min_history: int = 20) -> CurveSignal:
    current = snapshot.records.get("2s10s_bp")
    if current is None or len(history) < min_history:
        return CurveSignal(signal_id=f"sig-{snapshot.snapshot_id}", snapshot_id=snapshot.snapshot_id, as_of=snapshot.as_of, spread_bp=current or Decimal("0"), mean_bp=Decimal("0"), stdev_bp=Decimal("0"), reason="insufficient_history_or_missing_curve", status=DecisionStatus.ABSTAIN)
    mu = Decimal(str(mean(history)))
    sigma = Decimal(str(pstdev(history)))
    if sigma <= Decimal("0.000001"):
        return CurveSignal(signal_id=f"sig-{snapshot.snapshot_id}", snapshot_id=snapshot.snapshot_id, as_of=snapshot.as_of, spread_bp=current, mean_bp=mu, stdev_bp=sigma, reason="zero_or_near_zero_history_variance", status=DecisionStatus.ABSTAIN)
    z = (current - mu) / sigma
    direction = "STEEPENER" if z < Decimal("-1.5") else "FLATTENER" if z > Decimal("1.5") else None
    status = DecisionStatus.APPROVED if direction else DecisionStatus.NO_TRADE
    return CurveSignal(signal_id=f"sig-{snapshot.snapshot_id}", snapshot_id=snapshot.snapshot_id, as_of=snapshot.as_of, spread_bp=current, mean_bp=mu, stdev_bp=sigma, z_score=z, direction=direction, reason="threshold_crossed" if direction else "inside_entry_band", status=status)
