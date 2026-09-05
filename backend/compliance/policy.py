from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.domain.models import DecisionStatus, RiskDecision, RunMode, TradeProposal


@dataclass(frozen=True)
class ComplianceDecision:
    status: DecisionStatus
    policy_version: str
    checks: dict[str, str]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, "policy_version": self.policy_version, "checks": self.checks, "reason": self.reason}


def check_proposal(proposal: TradeProposal, risk: RiskDecision, mode: RunMode, now: datetime | None = None) -> ComplianceDecision:
    now = now or datetime.now(timezone.utc)
    checks = {"mode_not_live": "PASS" if mode in {RunMode.DEMO, RunMode.REPLAY, RunMode.PAPER} else "FAIL", "risk_approved": "PASS" if risk.status == DecisionStatus.APPROVED else "FAIL", "risk_not_expired": "PASS" if risk.expires_at > now else "FAIL", "proposal_snapshot": "PASS" if proposal.snapshot_id else "FAIL"}
    failures = [key for key, value in checks.items() if value != "PASS"]
    return ComplianceDecision(DecisionStatus.APPROVED if not failures else DecisionStatus.REJECTED, "compliance-policy-v1", checks, "PASS" if not failures else ";".join(failures))
