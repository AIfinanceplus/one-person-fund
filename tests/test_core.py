import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.contracts.roles import ROLE_CONTRACTS
from backend.domain.models import DataSnapshot, RunMode, Side, TradeLeg, TradeProposal
from backend.execution.paper import PaperBroker
from backend.ledger.accounting import Ledger
from backend.orchestration.demo import run_demo
from backend.orchestration.persistent import run_persistent_demo
from backend.risk.engine import RiskEngine
from backend.state.store import StateStore
from backend.data.time_series import FredGraphCsvSource, TreasuryXmlSource
from backend.orchestration.full_run import run_full_demo
from backend.orchestration.modes import run_replay


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

    def test_state_store_deduplicates_events_and_recovers_expired_task(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite3"
            store = StateStore(path)
            self.assertTrue(store.create_run("r1", "DEMO"))
            self.assertTrue(store.enqueue_task("t1", "r1", "R02", {"x": 1}))
            self.assertTrue(store.claim_task("t1", "worker-1", lease_seconds=0))
            self.assertTrue(store.claim_task("t1", "worker-2", lease_seconds=60))
            self.assertTrue(store.append_event("e1", "r1", 1, "TEST", {"ok": True}))
            self.assertFalse(store.append_event("e1", "r1", 1, "TEST", {"ok": True}))
            self.assertEqual(len(store.events("r1")), 1)
            store.close()
            reopened = StateStore(path)
            self.assertEqual(reopened.run("r1")["run_id"], "r1")
            self.assertEqual(reopened.task("t1")["attempt"], 2)
            reopened.close()

    def test_persistent_demo_writes_run_and_events(self):
        with TemporaryDirectory() as directory:
            result = run_persistent_demo(Path(directory) / "demo.sqlite3")
            self.assertEqual(result["status"], "SUCCEEDED")
            self.assertEqual(result["durable_run"]["status"], "SUCCEEDED")
            self.assertEqual(len(result["events"]), 2)

    def test_fred_csv_parser_keeps_missing_values_out(self):
        csv_text = "observation_date,TEST\n2026-01-01,1.25\n2026-02-01,.\n"
        points = FredGraphCsvSource(lambda _: csv_text).fetch("TEST")
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].value, Decimal("1.25"))
        self.assertIsNone(points[0].source_available_at)

    def test_treasury_xml_parser_builds_curve_snapshot_with_explicit_availability(self):
        xml = """<feed xmlns:d='urn:treasury'><entry><d:NEW_DATE>2026-09-04</d:NEW_DATE><d:BC_2YEAR>3.50</d:BC_2YEAR><d:BC_10YEAR>4.00</d:BC_10YEAR></entry></feed>"""
        source = TreasuryXmlSource(lambda _: xml)
        record = source.fetch_year(2026)[0]
        snapshot = source.snapshot(record, datetime(2026, 9, 4, 21, tzinfo=timezone.utc))
        self.assertEqual(snapshot.records["2s10s_bp"], Decimal("50.00"))
        self.assertEqual(snapshot.source, "treasury.gov:daily_treasury_yield_curve")

    def test_full_demo_exposes_all_pods_portfolio_compliance_and_fundbench(self):
        result = run_full_demo()
        artifacts = result["artifacts"]
        self.assertEqual(len(artifacts["pods"]), 5)
        self.assertEqual(artifacts["portfolio"]["status"], "PROPOSED")
        self.assertEqual(artifacts["compliance"]["status"], "APPROVED")
        self.assertEqual(artifacts["fundbench"]["completion_rate"], 1.0)

    def test_replay_uses_fixture_snapshot_and_keeps_mode_separate(self):
        result = run_replay("data/fixtures/curve_demo.json")
        self.assertEqual(result["run_id"], "replay-fixture-curve-001")
        self.assertEqual(result["artifacts"]["snapshot"]["mode"], "REPLAY")


if __name__ == "__main__":
    unittest.main()
