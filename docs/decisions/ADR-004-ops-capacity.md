# ADR-004: Review capacity sized to the book

**Decision.** Capacity is 1.5 analysts × 40 reviews = **60 reviews per business day**. An alert raised on a
weekend lands in Monday's queue. A business with several alerts on one day is one review.

**Why.** The original idea was 3 × 40 = 120 a day. With 8,000 businesses, no sensible rule set comes near
that, so ops load would never constrain anything. Sizing the team to the book makes capacity a real
trade-off.

**Observed.** The champion runs under capacity most of the year but goes over it in spring, when seasonal
businesses ramp up. That seasonality is a finding, not something I tuned for.
