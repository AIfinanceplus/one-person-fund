from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleContract:
    role_id: str
    title: str
    mission: str
    outputs: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    executor: str


ROLE_CONTRACTS: tuple[RoleContract, ...] = (
    RoleContract("R01", "Chief of Staff", "Route events and recover tasks", ("RunPlan", "TaskRun"), ("approve_trade", "change_policy"), "deterministic"),
    RoleContract("R02", "Data Steward", "Create validated, time-aware snapshots", ("DataSnapshot", "QualityReport"), ("invent_missing_values", "rewrite_raw_data"), "deterministic"),
    RoleContract("R03", "Macro Analyst", "Interpret growth, labor, credit and fiscal state", ("MacroState",), ("submit_order",), "model_plus_evidence"),
    RoleContract("R04", "Inflation Analyst", "Maintain CPI and PCE research", ("InflationPacket",), ("approve_trade",), "model_plus_evidence"),
    RoleContract("R05", "Fed Analyst", "Maintain policy scenarios and triggers", ("FedScenarioPacket",), ("invent_market_probability",), "model_plus_evidence"),
    RoleContract("R06", "Rates Strategist", "Generate rates signals and theses", ("Signal", "ThesisPacket"), ("submit_order", "approve_trade"), "deterministic_plus_explanation"),
    RoleContract("R07", "Quant Researcher", "Test hypotheses out of sample", ("ValidationReport",), ("change_frozen_test",), "deterministic"),
    RoleContract("R08", "Red Team", "Find contradictory evidence and failure modes", ("ChallengeReport",), ("rewrite_evidence",), "model_plus_evidence"),
    RoleContract("R09", "Portfolio Manager", "Rank opportunities and propose weights", ("PortfolioProposal", "TradeProposal"), ("bypass_risk", "submit_order"), "deterministic_plus_explanation"),
    RoleContract("R10", "Risk Manager", "Apply independent limits and stress checks", ("RiskDecision",), ("soften_rule_to_pass",), "deterministic"),
    RoleContract("R11", "Execution Trader", "Send only authorized paper orders", ("Order", "Fill"), ("change_approved_quantity", "live_order"), "deterministic"),
    RoleContract("R12", "Operations", "Reconcile fills, positions, cash and NAV", ("ReconciliationReport", "PnLAttribution"), ("silently_adjust_history",), "deterministic"),
    RoleContract("R13", "Compliance", "Check mode, instruments and authorization chain", ("PolicyDecision",), ("waive_required_gate",), "deterministic"),
    RoleContract("R14", "Auditor / Evaluator", "Measure task and strategy reliability", ("EvaluationReport",), ("rewrite_history", "auto_promote_permissions"), "deterministic_plus_summary"),
)


def role_registry() -> dict[str, RoleContract]:
    return {role.role_id: role for role in ROLE_CONTRACTS}
