# ADR-019: Risk Ops: cases, priority, and a capacity-limited queue

**Cases.** One case per business per review day, per rule set (`backtest.ops_cases`). A weekend alert lands in
Monday's queue (ADR-004). A case carries its rules, reason codes, strongest action, exposure and priority.

**Priority = exposure × likelihood. Neither reads the answer key.**
- **Exposure** comes from raw data: the payment or deposit amount; for an application, its stated monthly
  revenue; for a credit decision, the line's current limit.
- **Likelihood** is the highest precision, among the case's rules, that the bank had measured on the training
  months using only labels known by month 12 (ADR-013). A floor of 0.1% keeps a rule with no known catches from
  ranking at zero.

The case table lives in `models/backtest/` because it carries truth columns used afterwards to grade the
simulation. The priority itself uses none of them.

**The queue** (`scripts/queue_sim.py`; Python because a day-to-day backlog is awkward in SQL):
- **Capacity:** 90 cases per business day (ADR-011).
- **Three orders:** prioritized (highest priority first), first in first out, and unlimited reviewers as a
  reference.
- **Review windows:** an unreviewed case lapses after its action's window: a hold auto-releases after 2
  business days, an RFI goes stale after 5, a decline must be made within 2. Decisions happen at 13:00 on the
  review day.
- **Grading:** a loss is stopped only by a *reviewed* case on the same fraud case. A hold or block counts if it
  was raised before the loss; an RFI counts at half (ADR-003) if decided before the loss. Good customers wait
  from the alert until the decision, or until their hold lapses.

**Feedback loop.** Reviewed cases are labelled on the decision day, with error: analysts clear 10% of fraud and
mark 2% of good cases as fraud. Unreviewed cases are labelled only when fraud is confirmed some other way
(`label_known_at`). Measured precision at 7, 30 and 90 days is compared with the truth, counting an unlabelled
case as not fraud (as a bank usually does).

**Assumptions to revisit:** one decision per case; the same capacity every day; no escalation tier; and the
analyst error rates, which are invented.
