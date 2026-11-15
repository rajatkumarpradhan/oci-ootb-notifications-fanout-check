"""FAN001-FAN004 rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .model import PENDING_STALE_DAYS, Snapshot


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    topic: str
    subject: str
    detail: str


def rule_no_active_subscribers(snapshot: Snapshot, as_of: date) -> list:
    """FAN001 HIGH: topic with zero ACTIVE subscriptions."""
    del as_of
    out = []
    for t in snapshot.topics:
        if not any(s.is_active() for s in t.subscriptions):
            out.append(
                Finding(
                    rule="FAN001",
                    severity="HIGH",
                    topic=t.display_name,
                    subject=t.display_name,
                    detail="topic has no ACTIVE subscriptions; anything published here reaches nobody",
                )
            )
    return out


def rule_stale_pending(snapshot: Snapshot, as_of: date) -> list:
    """FAN002 MEDIUM: subscription PENDING longer than PENDING_STALE_DAYS."""
    out = []
    for t in snapshot.topics:
        for s in t.subscriptions:
            days = s.pending_days(as_of)
            if days is not None and days > PENDING_STALE_DAYS:
                out.append(
                    Finding(
                        rule="FAN002",
                        severity="MEDIUM",
                        topic=t.display_name,
                        subject=s.endpoint,
                        detail=f"{s.protocol} subscription PENDING for {days} days (> {PENDING_STALE_DAYS}); confirmation never completed",
                    )
                )
    return out


def rule_unreferenced_topic(snapshot: Snapshot, as_of: date) -> list:
    """FAN003 MEDIUM: topic not referenced by any Events rule."""
    del as_of
    out = []
    for t in snapshot.topics:
        if not t.referenced_by_rule:
            out.append(
                Finding(
                    rule="FAN003",
                    severity="MEDIUM",
                    topic=t.display_name,
                    subject=t.display_name,
                    detail="no Events rule references this topic; nothing will ever publish to it",
                )
            )
    return out


def rule_insecure_endpoint(snapshot: Snapshot, as_of: date) -> list:
    """FAN004 LOW: http:// (not https) endpoint."""
    del as_of
    out = []
    for t in snapshot.topics:
        for s in t.subscriptions:
            if s.protocol.lower() == "https" and s.endpoint.lower().startswith("http://"):
                out.append(
                    Finding(
                        rule="FAN004",
                        severity="LOW",
                        topic=t.display_name,
                        subject=s.endpoint,
                        detail="webhook endpoint is plain http://; alert payloads travel unencrypted",
                    )
                )
    return out


ALL_RULES = (
    rule_no_active_subscribers,
    rule_stale_pending,
    rule_unreferenced_topic,
    rule_insecure_endpoint,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(snapshot: Snapshot, as_of: date) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(snapshot, as_of))
    findings.sort(key=lambda f: (_SEVERITY_RANK[f.severity], f.rule, f.topic, f.subject))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
