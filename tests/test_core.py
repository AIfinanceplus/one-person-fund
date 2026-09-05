import unittest
from datetime import datetime, timezone
from decimal import Decimal

from backend.contracts.roles import ROLE_CONTRACTS
from backend.domain.models import DataSnapshot, RunMode, Side, TradeLeg, TradeProposal
from backend.execution.paper import PaperBroker
from backend.ledger.accounting import Ledger
from backend.orchestration.demo import run_demo
from backend.risk.engine import RiskEngine


class RatesFundCoreTests(unittest.TestCase):
    def test_all_roles_are_registered_once(self):
        ids = [role.role_id for role in ROLE_CONTRACTS]
        self.assertEqual(len(ids), 14)
        self.assertEqual(len(ids), len(set(ids)))

    def test_demo_completes_with_fills_and_ledger(self):
        result = run_demo()
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(len(result["artifacts"]["fills"]), 2)
        self.assertEqual(result["artifacts"]["ledger"]["entry_count"], 2)

    def test_duplicate_client_order_is_idempotent(self):
        broker = PaperBroker(RunMode.DEMO)
        leg = TradeLeg(instrument="SHY", side=Side.BUY, quantity=Decimal("10"))
        first, fill1 = broker.submit("p", leg, Decimal("82"), "client-1")
        second, fill2 = broker.submit("p", leg, Decimal("82"), "client-1")
        self.assertEqual(first.order_id, second.order_id)
        self.assertEqual(fill1.fill_id, fill2.fill_id)
        self.assertEqual(len(broker.orders), 1)

    def test_risk_rejects_unapproved_instrument(self):
        now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        proposal = TradeProposal(proposal_id="p", thesis_id="t", strategy_id="s", snapshot_id="snap", created_at=now, legs=[TradeLeg(instrument="BTC", side=Side.BUY, quantity=Decimal("1"))], target_weights={}, reason="test")
        decision = RiskEngine().check(proposal, {}, {}, {}, Decimal("10000000"), now)
        self.assertEqual(decision.status, "REJECTED")
        self.assertIn("instrument_not_approved:BTC", decision.reason)

    def test_risk_rejects_a_new_short_in_long_only_policy(self):
        now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        proposal = TradeProposal(proposal_id="p", thesis_id="t", strategy_id="s", snapshot_id="snap", created_at=now, legs=[TradeLeg(instrument="IEF", side=Side.SELL, quantity=Decimal("1"))], target_weights={}, reason="test")
        decision = RiskEngine().check(proposal, {}, {"IEF": Decimal("95")}, {"IEF": Decimal("7.2")}, Decimal("10000000"), now)
        self.assertEqual(decision.status, "REJECTED")
        self.assertIn("short_not_allowed:IEF", decision.reason)

    def test_ledger_replaying_same_fill_does_not_change_cash_twice(self):
        broker = PaperBroker(RunMode.DEMO)
        leg = TradeLeg(instrument="SHY", side=Side.BUY, quantity=Decimal("10"))
        _, fill = broker.submit("p", leg, Decimal("82"), "client-1")
        ledger = Ledger(Decimal("10000000"))
        ledger.record_fill(fill)
        cash_once = ledger.cash()
        ledger.record_fill(fill)
        self.assertEqual(ledger.cash(), cash_once)


if __name__ == "__main__":
    unittest.main()
