# ADR-014: The month-12 pattern is found by monitoring, then answered by a rule

**The pattern.** First-party ACH return fraud starts in month 12. A business pulls money in by ACH debit from
accounts it doesn't control, sends most of it out once available, and the debits return days later as
unauthorized. Legitimate ACH debits (owners topping up the business) exist all along, so the rail itself is
not suspicious.

**Monitoring.** No fraud labels are used (`models/monitoring/`). Every return series (rail × return reason) is
compared each week with its own trailing 12 weeks. An alarm fires at 3 or more returns that are more than 3
standard deviations above the trailing mean, with the deviation floored at 1. Many alarms fire over the
window, mostly bursts of bad checks. The first alarm on unauthorized ACH-debit returns is the one that
matters.

**The answer.** R9 is R1's logic applied to ACH debits.
- Its cutoff (0.4) is R1's shipped cutoff. I set it from alert volume, not tuned against labels: there were
  almost no confirmed cases to tune on.
- It goes live 10 business days after the alarm becomes visible (`mon_rule_effective_from`). The challenger
  gets credit only from then.
- The live date is computed, not typed in, so a different world moves it.

**Honest caveat.** R5 already caught part of this pattern by luck: the money often went to the owner's own
account at an unusual size. INV-001 says so.
