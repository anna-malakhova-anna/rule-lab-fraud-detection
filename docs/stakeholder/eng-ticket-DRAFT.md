# DRAFT: Engineering ticket: ship the credit rules

> **DRAFT. Numbers and rule definitions are generated from config and the warehouse by `make results`; the prose is
> mine to write.** Synthetic data. Bracketed notes are prompts, not text to keep.

## Events to log

<!-- eng-events:start -->
| Rule | Fields it reads (must be logged and available at decision time) |
|---|---|
| R10 Inflows ramped before a credit decision | `event_type`, `inflow_last_30d`, `baseline_monthly_inflow_31_120d`, `share_last_30d_from_new_payers` |
| R11 Credit draw money out fast | `out_48h_incl_this`, `normal_week_outflow`, `line_draws_prior_72h` |
| R12 Line drawn to limit soon after increase | `amount`, `utilisation_after`, `current_limit`, `days_since_limit_increase` |
<!-- eng-events:end -->

## Limits and cutoffs to enforce

<!-- eng-limits:start -->
| Rule | Score | Cutoff | Fixed gates | Action |
|---|---|---|---|---|
| R10 Inflows ramped before a credit decision | last 30 days of inflow / average month of the 90 days before that | >= 3 (tuned) | min_recent_inflow = 5000 | rfi |
| R11 Credit draw money out fast | share of the last 72 hours of line draws that left in the last 48 hours on top of a normal week of the account's spending | >= 0.3 (tuned) | min_recent_draws = 2000 | hold |
| R12 Line drawn to limit soon after increase | days since the limit was last raised | <= 14 (tuned) | min_utilisation = 0.8 | hold |
<!-- eng-limits:end -->

## Rollout and kill switch

<!-- eng-rollout:start -->
| Rule | Shadow mode | Expected cases/day | Kill switch if cases/day exceed |
|---|---|---|---|
| R10 Inflows ramped before a credit decision | 10 business days | 0.4 | 1.2 |
| R11 Credit draw money out fast | 10 business days | 2.5 | 7.5 |
| R12 Line drawn to limit soon after increase | 10 business days | 0.1 | 0.4 |
<!-- eng-rollout:end -->

[How the kill switch works: the rule's `status` in config/rules.yaml, how fast a change takes effect, who can flip it.]

## Acceptance

[What "done" means: rule hits match the backtest on the shadow period, the reason codes appear in the queue, the playbooks are linked.]
