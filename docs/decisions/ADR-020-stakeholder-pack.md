# ADR-020: The stakeholder pack is built on the current recommendation

**Decision.** Module B's three documents (`docs/stakeholder/`) present one recommendation: add the proposed
credit rules R10 to R12 to the running rule set (ADR-016). The handover suggested the Phase 1 recommendation,
but those numbers are frozen from a smaller, older world, and the change they describe is already in the
champion. A pack built on them couldn't be checked against the warehouse.

**Generated vs written.**
- *Generated* by `make results` and tested against the warehouse: every number, every rule definition, the
  fields each rule reads (taken from the rule's own evidence list, so the engineering ticket can't drift from
  the SQL), and the rollout table.
- *Mine to write:* the prose, marked DRAFT.

**Rollout parameters** (`config/backtest.yaml` `rollout`): 10 business days in shadow mode, then live. The
kill switch trips if a rule's daily cases exceed 3× what the backtest expects. Both are invented starting
points.
