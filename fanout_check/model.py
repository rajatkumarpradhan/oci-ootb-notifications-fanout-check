"""Data model + snapshot loading for Notifications fan-out checks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime


class SnapshotError(ValueError):
    """Raised when a snapshot file is malformed."""


PENDING_STALE_DAYS = 3
SUB_STATES = ("ACTIVE", "PENDING", "DELETED")


def parse_date(value: str, what: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"invalid date for {what}: {value!r} (expected YYYY-MM-DD)") from exc


@dataclass(frozen=True)
class Subscription:
    protocol: str
    endpoint: str
    state: str
    created_at: date

    def is_active(self) -> bool:
        return self.state.upper() == "ACTIVE"

    def pending_days(self, as_of: date) -> int | None:
        if self.state.upper() != "PENDING":
            return None
        return (as_of - self.created_at).days


@dataclass(frozen=True)
class Topic:
    ocid: str
    display_name: str
    referenced_by_rule: bool
    subscriptions: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class Snapshot:
    topics: tuple


def load_snapshot(path: str) -> Snapshot:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SnapshotError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("topics"), list):
        raise SnapshotError(f"{path}: top level must be an object with a 'topics' list")
    topics = []
    for i, t in enumerate(raw["topics"]):
        where = f"topics[{i}]"
        for req in ("ocid", "display_name"):
            if req not in t:
                raise SnapshotError(f"{where}: missing required field {req!r}")
        subs = []
        for j, s in enumerate(t.get("subscriptions", [])):
            swhere = f"{where}.subscriptions[{j}]"
            for req in ("protocol", "endpoint", "state", "created_at"):
                if req not in s:
                    raise SnapshotError(f"{swhere}: missing required field {req!r}")
            if s["state"].upper() not in SUB_STATES:
                raise SnapshotError(f"{swhere}: unknown state {s['state']!r}")
            subs.append(
                Subscription(
                    protocol=s["protocol"],
                    endpoint=s["endpoint"],
                    state=s["state"],
                    created_at=parse_date(s["created_at"], f"{swhere}.created_at"),
                )
            )
        topics.append(
            Topic(
                ocid=t["ocid"],
                display_name=t["display_name"],
                referenced_by_rule=bool(t.get("referenced_by_rule", False)),
                subscriptions=tuple(subs),
            )
        )
    return Snapshot(topics=tuple(topics))
