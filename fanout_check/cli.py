"""python -m fanout_check.cli SNAPSHOT [--as-of YYYY-MM-DD]"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from .model import SnapshotError, load_snapshot
from .rules import exit_code, run_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="notifications-fanout-check",
        description="Check an offline snapshot of OCI Notifications topics for fan-out gaps.",
    )
    p.add_argument("snapshot", help="path to the JSON topic snapshot")
    p.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default: today, UTC)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()
        except ValueError:
            print(f"error: --as-of {args.as_of!r} is not YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        as_of = date.today()
    try:
        snapshot = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = run_all(snapshot, as_of)
    subs = sum(len(t.subscriptions) for t in snapshot.topics)
    print(f"Notifications fan-out check as of {as_of.isoformat()} - {len(snapshot.topics)} topic(s), {subs} subscription(s), {len(findings)} finding(s)")
    for f in findings:
        print(f"[{f.severity:6s}] {f.rule} topic={f.topic} subject={f.subject}")
        print(f"         {f.detail}")
    code = exit_code(findings)
    print({0: "RESULT: clean", 1: "RESULT: warnings only", 2: "RESULT: HIGH findings present"}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
