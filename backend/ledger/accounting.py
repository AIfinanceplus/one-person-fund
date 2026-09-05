from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from backend.domain.models import Fill, LedgerEntry, Side


class Ledger:
    def __init__(self, initial_cash: Decimal, initial_positions: dict[str, Decimal] | None = None):
        self.initial_cash = initial_cash
        self.initial_positions = dict(initial_positions or {})
        self.entries: dict[str, LedgerEntry] = {}

    def record_fill(self, fill: Fill) -> LedgerEntry:
        if fill.fill_id in self.entries:
            return self.entries[fill.fill_id]
        sign = Decimal("1") if fill.side == Side.BUY else Decimal("-1")
        entry = LedgerEntry(entry_id=f"entry-{fill.fill_id}", event_id=fill.fill_id, account="PAPER", instrument=fill.instrument, quantity_delta=sign * fill.quantity, cash_delta=-sign * fill.quantity * fill.price - fill.fee, event_time=fill.event_time)
        self.entries[fill.fill_id] = entry
        return entry

    def positions(self) -> dict[str, Decimal]:
        result: dict[str, Decimal] = dict(self.initial_positions)
        for entry in self.entries.values():
            result[entry.instrument] = result.get(entry.instrument, Decimal("0")) + entry.quantity_delta
        return {key: value for key, value in result.items() if value != 0}

    def cash(self) -> Decimal:
        return self.initial_cash + sum(entry.cash_delta for entry in self.entries.values())

    def nav(self, marks: dict[str, Decimal]) -> Decimal:
        return self.cash() + sum(quantity * marks[instrument] for instrument, quantity in self.positions().items() if instrument in marks)

    def snapshot(self, marks: dict[str, Decimal]) -> dict[str, object]:
        return {"cash": str(self.cash()), "positions": {k: str(v) for k, v in self.positions().items()}, "nav": str(self.nav(marks)), "entry_count": len(self.entries)}
