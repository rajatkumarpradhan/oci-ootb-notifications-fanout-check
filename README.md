# oci-ootb-notifications-fanout-check

**Category: OOTB project - built from named built-in OCI services.** The *custom portfolio tool*
in this daily pair is `oci-oke-version-skew-check`; this repo is the one that wires native
platform services.

## Built-in OCI services wired

**OCI Events** (alarm/event rules) **+ OCI Notifications** (topics and subscriptions).
`terraform/` declares the native service configuration:

- `oci_events_rule` - routes OCI Monitoring alarm state changes into the topic
- `oci_ons_notification_topic` - the fan-out topic alerts are published to
- `oci_ons_subscription` - email and HTTPS webhook subscribers on that topic

That is the "OOTB" part: event matching, publishing and delivery are native OCI capabilities,
not code written here.

## Custom code (what this repo adds)

The pipeline is only as good as its last hop: a topic with no confirmed subscribers is an alarm
that fires into the void. `fanout_check/` is a custom Python checker that reads an **offline
snapshot** of topics and subscriptions and applies four rules:

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| FAN001 | HIGH | A topic has zero `ACTIVE` subscriptions - alerts publish to nobody. |
| FAN002 | MEDIUM | A subscription has been stuck `PENDING` (unconfirmed) for more than 3 days. |
| FAN003 | MEDIUM | A topic is not referenced by any Events rule - nothing ever publishes to it. |
| FAN004 | LOW | A subscription endpoint uses plain `http://` instead of `https://`. |

Exit code: `2` if any HIGH finding, `1` if only MEDIUM/LOW, `0` when clean.

## Run it

```bash
python -m fanout_check.cli samples/topics_messy.json --as-of 2026-11-16   # exits 2, all 4 rules fire
python -m fanout_check.cli samples/topics_clean.json --as-of 2026-11-16   # exits 0
```

`--as-of` fixes the reference date so PENDING-age math is reproducible; omit it for today (UTC).

## Test it

```bash
python -m unittest discover -s tests -v   # 19 tests, stdlib only
```

## What actually ran vs template-only

- **Ran (locally + CI):** the Python checker - 19 unit tests green on Python 3.10/3.11/3.12, and
  both demo invocations above execute as CI steps with asserted exit codes.
- **Template-only:** the Terraform in `terraform/` is **NOT plan/apply validated** - no topic,
  subscription, or Events rule was created, and no message was published or delivered.
- The sample topic JSON is synthetic; no live tenancy data is included.

## Honest limits

- Offline check of a static snapshot; it does not call the ONS or Events APIs.
- The 3-day PENDING window (FAN002) is a default, not an OCI policy; make it a flag before
  adopting in a real review.
- FAN003 relies on the snapshot's `referenced_by_rule` flag being populated by whatever produced
  the export; the checker cannot see Events rules itself.
- FAN001 means "this topic currently delivers nowhere" - it is a config finding, not a claim
  that alerts are being missed right now (nothing may be publishing).

## Layout

```
fanout_check/   custom Python: model, rules, CLI
terraform/      OCI Events rule + ONS topic + subscriptions (NOT plan/apply validated)
samples/        synthetic topic snapshots
tests/          19 stdlib unit tests
```

No paid services, no live cloud calls, no accounts created.
