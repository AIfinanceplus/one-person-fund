from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from backend.domain.models import DataSnapshot, RunMode


def read_paper_snapshot(path: str | Path) -> tuple[DataSnapshot, list[Decimal]]:
    """Read a user-supplied PAPER snapshot only when it declares its provenance."""
    payload = json.loads(Path(path).read_text())
    if payload.get("market_data_confirmed") is not True:
        raise ValueError("PAPER snapshot must set market_data_confirmed=true")
    source = str(payload.get("source", ""))
    if not source or source.startswith("fixture"):
        raise ValueError("PAPER snapshot needs a non-fixture market data source")
    data = payload["snapshot"]
    snapshot = DataSnapshot(snapshot_id=data["snapshot_id"], mode=RunMode.PAPER, as_of=datetime.fromisoformat(data["as_of"]), available_at=datetime.fromisoformat(data["available_at"]), source=source, records={key: Decimal(str(value)) for key, value in data["records"].items()}, quality=data.get("quality", "OK"), content_hash=data["content_hash"])
    if snapshot.available_at > snapshot.as_of and snapshot.available_at.tzinfo is None:
        raise ValueError("PAPER timestamps must include timezone")
    history = [Decimal(str(value)) for value in payload.get("history", [])]
    if len(history) < 20:
        raise ValueError("PAPER snapshot needs at least 20 eligible curve observations")
    return snapshot, history
