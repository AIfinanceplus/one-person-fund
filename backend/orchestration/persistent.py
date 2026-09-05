from __future__ import annotations

import json
from pathlib import Path

from backend.orchestration.demo import run_demo
from backend.state.store import StateStore


def run_persistent_demo(db_path: str | Path, run_id: str = "persistent-demo-001") -> dict[str, object]:
    """Run the deterministic demo while persisting task, artifact, and event state."""
    store = StateStore(db_path)
    store.create_run(run_id, "DEMO")
    store.enqueue_task(f"{run_id}:data", run_id, "R02", {"kind": "fixture_snapshot"})
    store.enqueue_task(f"{run_id}:curve", run_id, "R06", {"kind": "curve_signal"})
    store.claim_task(f"{run_id}:data", "demo-worker")
    result = run_demo()
    store.put_artifact(f"{run_id}:result", run_id, "RunResult", result)
    store.append_event(f"{run_id}:event:1", run_id, 1, "RUN_STARTED", {"mode": "DEMO"})
    store.append_event(f"{run_id}:event:2", run_id, 2, "RUN_RESULT", {"status": result["status"]})
    store.complete_task(f"{run_id}:data", "SUCCEEDED", f"{run_id}:result")
    store.claim_task(f"{run_id}:curve", "demo-worker")
    store.complete_task(f"{run_id}:curve", "SUCCEEDED", f"{run_id}:result")
    store.set_run_status(run_id, result["status"])
    result["durable_run"] = store.run(run_id)
    result["events"] = store.events(run_id)
    result["task_after_restart"] = store.task(f"{run_id}:curve")
    store.close()
    return result
