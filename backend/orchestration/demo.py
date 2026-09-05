from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from backend.contracts.roles import ROLE_CONTRACTS
from backend.domain.models import DataSnapshot, DecisionStatus, RunMode, RunSummary, Side, TradeLeg, TradeProposal
from backend.execution.paper import PaperBroker
from backend.ledger.accounting import Ledger
from backend.risk.engine import RiskEngine
from backend.strategies.curve_rv import curve_signal


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def build_demo_snapshot() -> tuple[DataSnapshot, list[Decimal]]:
    history = [Decimal(str(value)) for value in range(-5, 15)]
    records = {"2s10s_bp": Decimal("-12"), "SHY": Decimal("82.00"), "IEF": Decimal("95.00")}
    snapshot = DataSnapshot(snapshot_id="demo-snapshot-001", mode=RunMode.DEMO, as_of=datetime(2026, 9, 5, tzinfo=timezone.utc), available_at=datetime(2026, 9, 5, 14, tzinfo=timezone.utc), source="fixture", records=records, content_hash=_hash(records))
    return snapshot, history


def run_demo() -> dict[str, object]:
    snapshot, history = build_demo_snapshot()
    signal = curve_signal(snapshot, history)
    # Seed a 50/50 long-only baseline. The signal moves it to 60/40; it does not create a short.
    ledger = Ledger(Decimal("1000"), initial_positions={"SHY": Decimal("60969.512195"), "IEF": Decimal("52626.315789")})
    broker = PaperBroker(RunMode.DEMO)
    risk = RiskEngine()
    artifacts: dict[str, object] = {"roles": [role.role_id for role in ROLE_CONTRACTS], "snapshot": snapshot.model_dump(mode="json"), "signal": signal.model_dump(mode="json")}
    if signal.status != DecisionStatus.APPROVED:
        return {"run_id": "demo-run-001", "status": "ABSTAINED", "artifacts": artifacts, "ledger": ledger.snapshot({"SHY": Decimal("82"), "IEF": Decimal("95")})}
    # The ETF expression is deliberately a simple long-only sleeve and is not a pure DV01-neutral curve trade.
    legs = [TradeLeg(instrument="SHY", side=Side.BUY, quantity=Decimal("12195.121951")), TradeLeg(instrument="IEF", side=Side.SELL, quantity=Decimal("10526.315789"))]
    proposal = TradeProposal(proposal_id="proposal-demo-001", thesis_id="thesis-demo-001", strategy_id="curve_rv", snapshot_id=snapshot.snapshot_id, created_at=snapshot.available_at, legs=legs, target_weights={"SHY": Decimal("0.60"), "IEF": Decimal("0.40")}, reason="demo threshold crossed")
    decision = risk.check(proposal, current_weights={"SHY": Decimal("0.50"), "IEF": Decimal("0.50")}, prices={"SHY": Decimal("82"), "IEF": Decimal("95")}, durations={"SHY": Decimal("1.8"), "IEF": Decimal("7.2")}, nav=Decimal("10000000"), current_cash=Decimal("1000"), now=snapshot.available_at)
    artifacts["proposal"] = proposal.model_dump(mode="json")
    artifacts["risk_decision"] = decision.model_dump(mode="json")
    if decision.status == DecisionStatus.APPROVED:
        for index, leg in enumerate(decision.approved_legs):
            _, fill = broker.submit(proposal.proposal_id, leg, snapshot.records[leg.instrument], f"demo-{proposal.proposal_id}-{index}")
            ledger.record_fill(fill)
        for fill in broker.fills.values():
            artifacts.setdefault("fills", []).append(fill.model_dump(mode="json"))
    artifacts["ledger"] = ledger.snapshot({"SHY": snapshot.records["SHY"], "IEF": snapshot.records["IEF"]})
    return {"run_id": "demo-run-001", "status": "SUCCEEDED" if decision.status == DecisionStatus.APPROVED else "REJECTED", "artifacts": artifacts}


def run_summary() -> RunSummary:
    result = run_demo()
    return RunSummary(run_id=result["run_id"], mode=RunMode.DEMO, status=result["status"], event_count=len(result["artifacts"]), artifact_ids=list(result["artifacts"].keys()))
