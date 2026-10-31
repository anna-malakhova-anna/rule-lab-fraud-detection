# ADR-005: Scale, prevalence and uncertainty

**Decision.** 8,000 businesses and about 1.2% of them with a planted case: 48 check-deposit fraud and 48 BEC,
96 in all. Every headline number on the test months gets a 90% bootstrap range. Resampling is by business,
1,000 replicates, seed 42, with the same draws for champion and challenger so their difference is paired.

**Why.** Real prevalence is low, so cases are few. With 27 test cases, one case can move recall by about
four points. Showing ranges keeps me from reading noise as a result.
