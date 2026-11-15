import unittest
from datetime import date

from fanout_check.model import Snapshot, Subscription, Topic
from fanout_check.rules import (
    exit_code,
    rule_insecure_endpoint,
    rule_no_active_subscribers,
    rule_stale_pending,
    rule_unreferenced_topic,
    run_all,
)

AS_OF = date(2026, 11, 16)


def sub(state="ACTIVE", protocol="HTTPS", endpoint="https://hooks.example.com/x", created="2026-10-01"):
    from fanout_check.model import parse_date

    return Subscription(protocol=protocol, endpoint=endpoint, state=state,
                        created_at=parse_date(created, "test"))


def topic(name="t1", subs=(), wired=True):
    return Topic(ocid="oc1.t." + name, display_name=name,
                 referenced_by_rule=wired, subscriptions=tuple(subs))


class TestFan001NoActive(unittest.TestCase):
    def test_fires_on_empty_topic(self):
        snap = Snapshot(topics=(topic(),))
        out = rule_no_active_subscribers(snap, AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_fires_when_only_pending(self):
        snap = Snapshot(topics=(topic(subs=[sub(state="PENDING")]),))
        self.assertEqual(len(rule_no_active_subscribers(snap, AS_OF)), 1)

    def test_quiet_with_one_active(self):
        snap = Snapshot(topics=(topic(subs=[sub(), sub(state="PENDING")]),))
        self.assertEqual(rule_no_active_subscribers(snap, AS_OF), [])


class TestFan002StalePending(unittest.TestCase):
    def test_fires_over_three_days(self):
        snap = Snapshot(topics=(topic(subs=[sub(state="PENDING", created="2026-11-10")]),))
        self.assertEqual(len(rule_stale_pending(snap, AS_OF)), 1)

    def test_boundary_three_days_quiet(self):
        snap = Snapshot(topics=(topic(subs=[sub(state="PENDING", created="2026-11-13")]),))
        self.assertEqual(rule_stale_pending(snap, AS_OF), [])

    def test_active_sub_ignored(self):
        snap = Snapshot(topics=(topic(subs=[sub(created="2026-01-01")]),))
        self.assertEqual(rule_stale_pending(snap, AS_OF), [])


class TestFan003Unwired(unittest.TestCase):
    def test_fires_when_unreferenced(self):
        snap = Snapshot(topics=(topic(wired=False),))
        out = rule_unreferenced_topic(snap, AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_quiet_when_wired(self):
        snap = Snapshot(topics=(topic(),))
        self.assertEqual(rule_unreferenced_topic(snap, AS_OF), [])


class TestFan004Insecure(unittest.TestCase):
    def test_fires_on_http_webhook(self):
        snap = Snapshot(topics=(topic(subs=[sub(endpoint="http://hooks.example.com/x")]),))
        self.assertEqual(len(rule_insecure_endpoint(snap, AS_OF)), 1)

    def test_case_insensitive_scheme(self):
        snap = Snapshot(topics=(topic(subs=[sub(endpoint="HTTP://hooks.example.com/x")]),))
        self.assertEqual(len(rule_insecure_endpoint(snap, AS_OF)), 1)

    def test_https_quiet(self):
        snap = Snapshot(topics=(topic(subs=[sub()]),))
        self.assertEqual(rule_insecure_endpoint(snap, AS_OF), [])

    def test_email_protocol_ignored(self):
        snap = Snapshot(topics=(topic(subs=[sub(protocol="EMAIL", endpoint="a@b.com")]),))
        self.assertEqual(rule_insecure_endpoint(snap, AS_OF), [])


class TestAggregation(unittest.TestCase):
    def test_exit_code_2_on_high(self):
        snap = Snapshot(topics=(topic(),))
        self.assertEqual(exit_code(run_all(snap, AS_OF)), 2)

    def test_exit_code_1_on_medium_only(self):
        snap = Snapshot(topics=(topic(subs=[sub()], wired=False),))
        self.assertEqual(exit_code(run_all(snap, AS_OF)), 1)

    def test_exit_code_0_when_clean(self):
        snap = Snapshot(topics=(topic(subs=[sub()]),))
        self.assertEqual(exit_code(run_all(snap, AS_OF)), 0)


if __name__ == "__main__":
    unittest.main()
