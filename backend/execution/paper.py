from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from backend.domain.models import Fill, Order, RunMode, Side, TradeLeg


class PaperBroker:
    """Deterministic, idempotent paper execution port for DEMO/REPLAY/PAPER."""

    def __init__(self, mode: RunMode = RunMode.DEMO, cost_bps: Decimal = Decimal("2")):
        if mode not in (RunMode.DEMO, RunMode.REPLAY, RunMode.PAPER):
            raise ValueError("live execution is not supported")
        self.mode = mode
        self.cost_bps = cost_bps
        self.orders: dict[str, Order] = {}
        self.fills: dict[str, Fill] = {}

    def submit(self, proposal_id: str, leg: TradeLeg, reference_price: Decimal, client_order_id: str) -> tuple[Order, Fill]:
        if client_order_id in self.orders:
            order = self.orders[client_order_id]
            fill = next(fill for fill in self.fills.values() if fill.order_id == order.order_id)
            return order, fill
        if reference_price <= 0:
            raise ValueError("reference price must be positive")
        impact = self.cost_bps / Decimal("10000")
        fill_price = reference_price * (Decimal("1") + impact if leg.side == Side.BUY else Decimal("1") - impact)
        order = Order(order_id=f"ord-{client_order_id}", client_order_id=client_order_id, proposal_id=proposal_id, instrument=leg.instrument, side=leg.side, quantity=leg.quantity, reference_price=reference_price, execution_mode=self.mode, status="FILLED")
        fill = Fill(fill_id=f"fill-{client_order_id}", order_id=order.order_id, instrument=leg.instrument, side=leg.side, quantity=leg.quantity, price=fill_price, fee=Decimal("0"), event_time=datetime.now(timezone.utc))
        self.orders[client_order_id] = order
        self.fills[fill.fill_id] = fill
        return order, fill
