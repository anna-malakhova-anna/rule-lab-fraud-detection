# DRAFT: Ops brief: what changes in the queue on Monday

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Synthetic data. Bracketed notes are prompts, not text to keep.

## New reason codes

<!-- ops-codes:start -->
| New reason code | Rule | Action | Expected cases per business day | Playbook |
|---|---|---|---|---|
| `CREDIT_INFLOW_RAMP` | R10 Inflows ramped before a credit decision | rfi | 0.4 | [playbook](../playbooks/R10_credit_inflow_ramp.md) |
| `CREDIT_DRAW_OUT_FAST` | R11 Credit draw money out fast | hold | 2.4 | [playbook](../playbooks/R11_draw_then_fast_out.md) |
| `CREDIT_FULL_DRAW` | R12 Line drawn to limit soon after increase | hold | 0.1 | [playbook](../playbooks/R12_full_draw_after_increase.md) |
<!-- ops-codes:end -->

## The queue

<!-- ops-queue:start -->
| Prioritized queue at 90 reviews/day (test months) | Today | With the change |
|---|---|---|
| Cases per business day | 85.9 | 88.5 |
| Cases that lapse unreviewed | 1,228 | 1,388 |
| Good customers held more than 24 hours | 491 | 542 |
| Fraud $ prevented | $4.01M | $4.89M |
<!-- ops-queue:end -->

## Playbook changes

[Which playbooks are new, what analysts check first, and how to escalate a suspected bust-out (freeze further draws).]

## Who to ask

[Owner for questions in the first two weeks.]
