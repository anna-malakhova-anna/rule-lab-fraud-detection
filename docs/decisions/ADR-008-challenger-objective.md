# ADR-008: How the challenger picks its cutoffs

**Decision.** For each rule, using training months only:
1. Drop cutoffs where the rule alone would use more than 50% of daily review capacity.
2. Pick the cutoff with the highest **net value**:
   fraud $ prevented − $30 × reviews − $150 × good businesses flagged − 0.05%/day × good dollar-days held
   − $1,000 × payrolls delayed.
3. Break ties toward the stricter cutoff. Retire a rule whose best net value is not positive.

**Why.** A single objective makes the choice reproducible and arguable. All costs are invented and live in
`config/backtest.yaml`. A different appetite for friction picks different cutoffs. The trade-off curves on
the results page show every option, not just the chosen one.

**Limit.** Each rule is tuned on its own. Rules overlap (`bt_rule_overlap`), so tuning them jointly might
choose differently.
