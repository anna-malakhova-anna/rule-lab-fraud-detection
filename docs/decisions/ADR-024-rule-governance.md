# ADR-024: Rule governance: inventory, change log enforced by the build, and a label-honest quarterly review

**Inventory** (`gov_rule_inventory`, `docs/governance/rule-register.md`, the Rules page): one row per rule with
owner, status, rationale, action, cutoff, last change and its decision record, test-month precision and volume,
cases only it caught, the latest review and a retirement trigger. Owners are invented team roles by rule family
(`owner` in `config/rules.yaml`).

**Change log** (`config/rule_changes.yaml`): every rule added and every cutoff, action, scope or status change,
with the ADR and the backtest that justified it, reconstructed from this project's history. A test fails if any
rule's cutoff or action differs from its latest entry, so a change cannot ship without its log line. Dates are the
days the changes were made in this project.

**Change template** (`docs/governance/rule-change-template-DRAFT.md`): what a proposed change must show before it
ships: backtest against today's rules, leave-one-out value, precision against break-even, ops load against
capacity, rollout (shadow mode, kill switch) and rollback.

**Quarterly review** (`gov_rule_quarterly`, config `config/governance.yaml`). After each quarter, each running rule
in the recommended set is judged with only the labels known 30 days after the quarter ends:
- **Retune** when its precision is below its **break-even precision** (`gov_break_even`): the precision at which its
  false alarms cost as much as the fraud it stops, from its own training-month value per true alert and cost per
  false alert at the cutoff it runs at. Derived from the stated costs, not a separate invented floor.
- **Retire candidate** when it adds no fraud dollars on top of the other rules for two reviews in a row. That is
  **leave one out**: the challenger minus that rule (`without:<rule>` rule sets, graded like every other rule set,
  with loss-level credit in `bt_loss_credit`). "Cases only this rule caught" is shown too, but it is not the
  trigger: it calls a rule useless when it catches the same case earlier, which is worth real dollars (ADR-022).
- **Investigate drift** when alerts per business day double or halve against the previous judged quarter.
- **Late labels.** Mule cases are confirmed about 70 days after they end and credit bust-outs about 160 days after
  (at charge-off), so R7 is judged on the alerts of one quarter back and R10 to R12 on two quarters back
  (`lag_quarters`). Without that, their missing labels looked like false alarms and every credit rule was flagged.
  The team would know these delays from its own confirmed cases.

**What the review shows.** A flag is a prompt for a person. R9 guards against ACH return fraud, which starts in month
12; in the reviews before that it adds nothing and is flagged as a retire candidate. Retiring it then would have
been a mistake.

**Housekeeping in this change.** The loss-credit model the launch review used became the shared `bt_loss_credit`.
`ops_cases` now covers only the two rule sets the Risk Ops queue is simulated for, so it does not grow with every
analysis rule set.
