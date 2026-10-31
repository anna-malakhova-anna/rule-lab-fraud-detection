# ADR-016: The line of credit, bust-out fraud, and honest defaults

**Product.** A revolving line of credit (`generator/credit.py`, config `credit`):
- A business becomes eligible after six months of account history; 35% of eligible businesses take a line.
- The limit is half the account's average monthly inflow over the 90 days before opening, between $2,000 and
  $150,000.
- Draws and repayments are transactions (`loc_draw`, `loc_repayment`). Line events go to raw
  `credit_line_events`.
- 15% of honest lines ask for one increase (×1.5). Seasonal businesses ask in March, ahead of their peak.

**Bust-out (fraud), 42 cases.** The sequence:
1. 2 to 7 months of clean use.
2. 3 to 6 weeks of round-trip money from outside accounts the owner controls, sent back to those same accounts.
3. A limit increase the policy grants on the inflated inflows.
4. The line drawn to 90 to 100% within days, then wired out within hours.

The loss is the money sent out. Labels arrive around charge-off, 150 to 180 days after the cash-out.

**Honest defaults (not fraud), 5% of honest lines.** Revenue falls away over 2 to 5 months, the line is drawn
to keep paying staff and suppliers, then the business stops, misses a payment and is charged off 120 days later.
- These businesses are good customers throughout. A hold on them is harm.
- `bt_credit_losses` reports them on their own line: how many defaulted, the balance, how much was flagged in
  the 90 days before, and the holds put on them. **None of it is added to fraud prevented.**

**Rules (challenger, tuned on training months with known labels):**
- R10: inflows ramped before a line opening or increase request. Action RFI: ask for financials before granting.
- R11: line-draw money leaving fast, above a normal week of spending (R1's logic on draws).
- R12: the line drawn to 80%+ of its limit soon after an increase.

**Baseline.** The Phase 2 challenger is the Phase 3 champion: R6 to R9 run with Phase 2's cutoffs and R6's
two-tier decline (ADR-015). R9 runs for the whole window, because it shipped. The Phase 2 memo and INV-001 are
frozen at commit 4b76799.

**Generator fix found while grading.** The first version sent round-trip money back to the owner's existing
account. That made R5 (payment far above usual to a payee) fire on every bust-out, a shortcut in my generator
rather than a finding. Round-trip money now goes back to the outside accounts it came from.

**Known simplification.** An RFI on an increase request is credited, like every RFI, with stopping half the
loss. In reality a fraudster whose increase is questioned might still draw the original limit.
