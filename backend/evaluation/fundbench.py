from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    category: str
    reason: str


@dataclass(frozen=True)
class FundBenchReport:
    dataset_version: str
    cases: tuple[CaseResult, ...]

    def as_dict(self) -> dict[str, Any]:
        by_category: dict[str, dict[str, int]] = {}
        for case in self.cases:
            bucket = by_category.setdefault(case.category, {"passed": 0, "total": 0})
            bucket["total"] += 1
            bucket["passed"] += int(case.passed)
        return {"dataset_version": self.dataset_version, "total": len(self.cases), "passed": sum(int(c.passed) for c in self.cases), "completion_rate": (sum(int(c.passed) for c in self.cases) / len(self.cases) if self.cases else 0), "by_category": by_category, "failures": [c.__dict__ for c in self.cases if not c.passed]}


def run_fundbench(run_demo: Callable[[], dict[str, Any]]) -> FundBenchReport:
    result = run_demo()
    artifacts = result.get("artifacts", {})
    cases = (
        CaseResult("roles-14", len(artifacts.get("roles", [])) == 14, "organization", "14 roles registered"),
        CaseResult("signal-present", "signal" in artifacts, "strategy", "curve signal artifact present"),
        CaseResult("risk-artifact", "risk_decision" in artifacts, "risk", "risk decision artifact present"),
        CaseResult("two-fills", len(artifacts.get("fills", [])) == 2, "execution", "two paper fills"),
        CaseResult("ledger-two-entries", artifacts.get("ledger", {}).get("entry_count") == 2, "accounting", "two ledger entries"),
        CaseResult("succeeded", result.get("status") == "SUCCEEDED", "orchestration", "run completed"),
    )
    return FundBenchReport("fundbench-v1-demo", cases)
