from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend.domain.models import DecisionStatus, RiskDecision, Side, TradeLeg, TradeProposal


@dataclass(frozen=True)
class RiskPolicy:
    version: str = "risk-policy-v1"
    initial_nav: Decimal = Decimal("10000000")
    max_gross_weight: Decimal = Decimal("1")
    max_single_weight: Decimal = Decimal("0.60")
    max_dv01: Decimal = Decimal("10000")
    daily_loss_freeze: Decimal = Decimal("-0.0075")
    approved_instruments: tuple[str, ...] = ("SHY", "IEF", "TLT", "TIP")


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()

    def check(
        self,
        proposal: TradeProposal,
        current_weights: dict[str, Decimal],
        prices: dict[str, Decimal],
        durations: dict[str, Decimal],
        nav: Decimal,
        now: datetime | None = None,
        current_cash: Decimal | None = None,
    ) -> RiskDecision:
        now = now or datetime.now(timezone.utc)
        checks: dict[str, str] = {}
        tolerance = Decimal("0.000001")
        failures: list[str] = []
        if proposal.snapshot_id == "":
            failures.append("missing_snapshot")
        if nav <= 0:
            failures.append("invalid_nav")
        gross = sum(abs(v) for v in current_weights.values())
        proposed_weights = dict(current_weights)
        for leg in proposal.legs:
            if leg.instrument not in self.policy.approved_instruments:
                failures.append(f"instrument_not_approved:{leg.instrument}")
                continue
            if leg.instrument not in prices or prices[leg.instrument] <= 0:
                failures.append(f"missing_price:{leg.instrument}")
                continue
            signed = leg.quantity * prices[leg.instrument] / nav
            proposed_weights[leg.instrument] = proposed_weights.get(leg.instrument, Decimal("0")) + (signed if leg.side == Side.BUY else -signed)
            checks[f"price:{leg.instrument}"] = "PASS"
        proposed_gross = sum(abs(v) for v in proposed_weights.values())
        checks["gross_weight"] = "PASS" if proposed_gross <= self.policy.max_gross_weight + tolerance else "FAIL"
        if proposed_gross > self.policy.max_gross_weight + tolerance:
            failures.append("gross_weight_limit")
        for instrument, weight in proposed_weights.items():
            checks[f"single_weight:{instrument}"] = "PASS" if abs(weight) <= self.policy.max_single_weight + tolerance else "FAIL"
            if abs(weight) > self.policy.max_single_weight + tolerance:
                failures.append(f"single_weight_limit:{instrument}")
            checks[f"long_only:{instrument}"] = "PASS" if weight >= 0 else "FAIL"
            if weight < 0:
                failures.append(f"short_not_allowed:{instrument}")
        dv01 = Decimal("0")
        for instrument, weight in proposed_weights.items():
            if instrument in durations:
                dv01 += abs(weight * nav * durations[instrument] * Decimal("0.0001"))
        checks["gross_dv01"] = "PASS" if dv01 <= self.policy.max_dv01 + tolerance else "FAIL"
        if dv01 > self.policy.max_dv01 + tolerance:
            failures.append("dv01_limit")
        if current_cash is not None:
            cash_after = current_cash
            for leg in proposal.legs:
                notional = leg.quantity * prices.get(leg.instrument, Decimal("0"))
                cash_after += notional if leg.side == Side.SELL else -notional
                cash_after -= notional * proposal.expected_cost_bps / Decimal("10000")
            checks["cash_nonnegative"] = "PASS" if cash_after >= -tolerance else "FAIL"
            if cash_after < -tolerance:
                failures.append("cash_negative_after_cost")
        status = DecisionStatus.APPROVED if not failures else DecisionStatus.REJECTED
        return RiskDecision(
            decision_id=f"risk-{proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
            status=status,
            policy_version=self.policy.version,
            checks=checks,
            approved_legs=proposal.legs if status == DecisionStatus.APPROVED else [],
            reason="PASS" if status == DecisionStatus.APPROVED else ";".join(failures),
            expires_at=now + timedelta(minutes=15),
        )
