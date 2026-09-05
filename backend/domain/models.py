from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunMode(StrEnum):
    DEMO = "DEMO"
    REPLAY = "REPLAY"
    PAPER = "PAPER"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class DecisionStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NO_TRADE = "NO_TRADE"
    ABSTAIN = "ABSTAIN"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class FundBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class DataSnapshot(FundBase):
    snapshot_id: str
    mode: RunMode
    as_of: datetime
    available_at: datetime
    source: str
    records: dict[str, Decimal]
    quality: str = "OK"
    content_hash: str

    @field_validator("as_of", "available_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamps must include a timezone")
        return value


class CurveSignal(FundBase):
    signal_id: str
    strategy_id: str = "curve_rv"
    snapshot_id: str
    as_of: datetime
    spread_bp: Decimal
    mean_bp: Decimal
    stdev_bp: Decimal
    z_score: Decimal
    direction: str | None = None
    status: DecisionStatus = DecisionStatus.NO_TRADE
    reason: str
    model_version: str = "curve-rv-v1"


class TradeLeg(FundBase):
    instrument: str
    side: Side
    quantity: Decimal = Field(gt=0)


class TradeProposal(FundBase):
    proposal_id: str
    thesis_id: str
    strategy_id: str
    snapshot_id: str
    created_at: datetime
    legs: list[TradeLeg]
    target_weights: dict[str, Decimal]
    expected_cost_bps: Decimal = Decimal("2")
    reason: str
    kill_conditions: list[str] = []


class RiskDecision(FundBase):
    decision_id: str
    proposal_id: str
    status: DecisionStatus
    policy_version: str
    checks: dict[str, str]
    approved_legs: list[TradeLeg] = []
    reason: str
    expires_at: datetime


class Order(FundBase):
    order_id: str
    client_order_id: str
    proposal_id: str
    instrument: str
    side: Side
    quantity: Decimal = Field(gt=0)
    reference_price: Decimal = Field(gt=0)
    execution_mode: RunMode
    status: str = "NEW"


class Fill(FundBase):
    fill_id: str
    order_id: str
    instrument: str
    side: Side
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fee: Decimal = Decimal("0")
    event_time: datetime


class LedgerEntry(FundBase):
    entry_id: str
    event_id: str
    account: str
    instrument: str
    quantity_delta: Decimal = Decimal("0")
    cash_delta: Decimal = Decimal("0")
    event_time: datetime


class RunSummary(FundBase):
    run_id: str
    mode: RunMode
    status: str
    event_count: int
    artifact_ids: list[str]
    warnings: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def utc(day: date, hour: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc)
