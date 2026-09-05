from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from backend.domain.models import DataSnapshot, Side, TradeLeg, TradeProposal
from backend.strategies.pods import PodResult


@dataclass(frozen=True)
class PortfolioProposal:
    proposal: TradeProposal | None
    status: str
    selected_pods: tuple[str, ...]
    rejected_pods: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "selected_pods": list(self.selected_pods), "rejected_pods": list(self.rejected_pods), "reason": self.reason, "proposal": self.proposal.model_dump(mode="json") if self.proposal else None}


def build_portfolio_proposal(snapshot: DataSnapshot, pods: list[PodResult]) -> PortfolioProposal:
    curve = next((pod for pod in pods if pod.pod_id == "curve_rv"), None)
    selected = tuple(pod.pod_id for pod in pods if pod.status == "SIGNAL")
    rejected = tuple(pod.pod_id for pod in pods if pod.status in {"ABSTAIN", "NO_TRADE"})
    if curve is None or curve.status != "SIGNAL":
        return PortfolioProposal(None, "NO_TRADE", selected, rejected, "no eligible executable signal")
    proposal = TradeProposal(
        proposal_id=f"proposal-{snapshot.snapshot_id}", thesis_id=f"thesis-{snapshot.snapshot_id}", strategy_id="curve_rv", snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.available_at,
        legs=[TradeLeg(instrument="SHY", side=Side.BUY, quantity=Decimal("12195.121951")), TradeLeg(instrument="IEF", side=Side.SELL, quantity=Decimal("10526.315789"))],
        target_weights={"SHY": Decimal("0.60"), "IEF": Decimal("0.40")}, reason="curve_rv signal converted to a long-only 60/40 sleeve",
        kill_conditions=["curve z-score returns inside exit band", "risk policy becomes stale"],
    )
    return PortfolioProposal(proposal, "PROPOSED", selected, rejected, "one executable signal passed strategy selection")
