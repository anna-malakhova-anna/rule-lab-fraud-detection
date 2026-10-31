# ADR-002: Tune on months 1-12, grade on months 13-18

**Decision.** Challenger cutoffs are picked using the first 12 months only. Champion and challenger are
compared on months 13 to 18. Ninety days of warm-up activity come before month 1 so baselines exist on day
one; the warm-up is never graded.

**Why.** If the sweep and the comparison used the same months, the challenger would win by construction:
it was fitted to those cases. A time split is also how this would work for real: you tune on the past and
live with the future.

**Cost.** The test period holds only about a quarter of the cases (27 of 96), so test numbers are noisy.
ADR-005 covers how I show that.
