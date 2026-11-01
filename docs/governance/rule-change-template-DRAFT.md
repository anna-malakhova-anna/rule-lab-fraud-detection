# DRAFT: Rule change request

> **DRAFT template. The wording is mine to finalise.** Copy this for any new rule, threshold, action or scope
> change. A change ships only with every section filled in, and with its entry in `config/rule_changes.yaml`
> (the build fails if a rule's cutoff or action differs from its latest change-log entry).

**Rule:** `R_` · **Owner:** · **Change:** added | threshold | action | scope | status | retired
**Decision record:** ADR-0__

## 1. What changes and why

- Before → after (cutoff, action, scope):
- The fraud pattern or customer harm it answers:
- How the cutoff was chosen (training months only; labels as known at the time, ADR-002, ADR-013):

## 2. Backtest results (held-out test months)

Against the rule set running today, from `bt_strategy_metrics` and the threshold sweep:

| | Today | With the change |
|---|---|---|
| Fraud $ prevented (90% range) | | |
| Precision | | |
| Good businesses flagged / held | | |
| Payrolls delayed | | |
| Good applicants declined | | |
| Net value at the stated costs | | |

- Fraud $ the rule adds on top of the others (leave one out):
- Precision against its break-even precision (`gov_break_even`):

## 3. Ops impact

- Reviews per business day, average and worst day, against capacity (90):
- Effect on the priority queue: who waits longer (`scripts/queue_sim.py`):
- Analyst playbook written or updated (`docs/playbooks/`):

## 4. Rollout and rollback

- Shadow mode: 10 business days logging what it would have done (config `rollout`).
- Kill switch: turned off if daily cases exceed 3× the backtest's expectation.
- Rollback: the previous cutoff and action, restored from the change log entry before this one.
- Who decides to roll back, and how fast:

## 5. Sign-off

- Rule owner:
- Risk Ops lead (capacity):
- Next quarterly review that will check it:
