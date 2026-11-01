# ADR-021: Instant payouts, the timing rule, and launch controls

**The product.** From 1 March 2026 (`config/generation.yaml` `instant_payouts`), outbound ACH and wire payments to
a payee (never payroll) can go out as `instant_payout`, up to $25,000 each.
- 30% of honest businesses adopt it, for 10 to 50% of their eligible payments.
- Fraudsters adapt: 85% of cash-outs after launch switch to instant, and a cash-out above the cap is split into
  several payouts minutes apart.

**The timing rule (the blind spot).** Rules score a payment after it posts. A standard payment can still be
held then; an instant payout has already gone. In grading (`loss_credit` macro), a loss sent instantly can be
stopped only by an alert strictly *before* it, such as a hold on the deposit that funded it. An alert on the
instant payout itself comes too late. `bt_launch_blind_spots` measures, per running rule, the fraud it
stopped before launch only by alerting on the cash-out itself.

**Launch controls (C1 to C4)** are rules with `status: launch_control`, checked before the payout is sent. Their
action is `delay`: the payout goes the standard way, so the other rules get their window back. A delay stops
nothing by itself and needs no analyst. The customer waits about a day, priced like any good business flagged
($150, ADR-008).
- C1: young accounts
- C2: new or changed payees
- C3: right after a contact change or new device
- C4: money that can still come back

Each control is graded alone (`launch:<rule>`) and all together (`launch_controls`), on top of today's rules.

**Simplifications.** A good customer's instant payout that a batch rule flags after it left still counts as a
flag, even though nothing was held. Fraudsters don't yet adapt to the controls themselves.
