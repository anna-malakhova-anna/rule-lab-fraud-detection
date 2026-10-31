# ADR-010: The Phase 1 challenger becomes the Phase 2 champion

**Decision.** For Phase 2 I assume the Phase 1 challenger shipped:
- R1 runs without payroll (ADR-009). The exclusion now lives in R1's own SQL.
- The five cutoffs are the ones Phase 1 tuned: R1 ≥ 0.4, R2 ≥ 0.5, R3 ≥ 5, R4 ≤ 7, R5 ≥ 4.

The Phase 2 challenger keeps those five unchanged and adds R6 to R9.

**Why.** Each phase's comparison should isolate that phase's changes. Comparing Phase 2 against the original
day-one rules would mix Phase 1 and Phase 2 improvements.

**Consequences.**
- The Phase 1 cutoffs were tuned on the 8,000-business world, not this one. They are "what shipped", not
  re-fitted.
- The Phase 1 memo's numbers are frozen (commit 6796339), because the world they describe was regenerated at
  12,000 businesses.
- The `challenger_scope` mechanism from ADR-009 is gone. Rules now carry a `status` instead.
