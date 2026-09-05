from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from backend.domain.models import DataSnapshot, RunMode


class FixtureSource:
    """Read a versioned, deterministic snapshot for DEMO or REPLAY runs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self, mode: RunMode = RunMode.REPLAY) -> tuple[DataSnapshot, list[Decimal]]:
        payload = json.loads(self.path.read_text())
        if mode not in (RunMode.DEMO, RunMode.REPLAY):
            raise ValueError("fixture source cannot create a PAPER snapshot")
        snapshot_data = payload["snapshot"]
        records = {key: Decimal(str(value)) for key, value in snapshot_data["records"].items()}
        snapshot = DataSnapshot(
            snapshot_id=snapshot_data["snapshot_id"], mode=mode,
            as_of=datetime.fromisoformat(snapshot_data["as_of"]),
            available_at=datetime.fromisoformat(snapshot_data["available_at"]),
            source=snapshot_data["source"], records=records,
            quality=snapshot_data.get("quality", "OK"), content_hash=snapshot_data["content_hash"],
        )
        history = [Decimal(str(value)) for value in payload["history"]]
        return snapshot, history
