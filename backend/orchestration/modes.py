from __future__ import annotations

from pathlib import Path

from backend.data.fixture_source import FixtureSource
from backend.data.paper_source import read_paper_snapshot
from backend.orchestration.demo import run_snapshot


def run_replay(fixture_path: str | Path) -> dict[str, object]:
    snapshot, history = FixtureSource(fixture_path).read()
    return run_snapshot(snapshot, history, run_id=f"replay-{snapshot.snapshot_id}")


def run_paper(snapshot_path: str | Path) -> dict[str, object]:
    snapshot, history = read_paper_snapshot(snapshot_path)
    return run_snapshot(snapshot, history, run_id=f"paper-{snapshot.snapshot_id}")
