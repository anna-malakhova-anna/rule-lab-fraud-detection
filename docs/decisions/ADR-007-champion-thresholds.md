# ADR-007: Champion thresholds were set before grading

**Decision.** The champion cutoffs in `config/rules.yaml` come from fraud intuition plus **alert volumes
only**. Alert volumes need no labels. I did not look at fraud caught before fixing them.

**One rule was redesigned from volume alone.** R1 first scored "48-hour outflow ÷ 72-hour check deposits".
That flagged every business that simply spends more than it takes in by check: about 100 alerts a day. I
changed the score to the share of fresh check money that left *on top of a normal week of the account's
spending*. Volume fell to about 14 a day. I made that change for a design reason (the first score measured
size, not the pattern), still without labels.

**Why it matters.** If the champion were tuned on the answer key, champion vs challenger would compare two
fitted rule sets, and the "today" baseline would look better than a real day-one rule set would.
