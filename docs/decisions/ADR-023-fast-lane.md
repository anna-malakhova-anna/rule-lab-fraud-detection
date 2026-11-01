# ADR-023: The good-customer fast lane softens, never skips, and its cap is left to judgement

**Where the friction is.** On the training months, alerts on businesses open at least a year with no returned
item in 180 days are fraud far less often than alerts on everyone else (`bt_fast_lane_segments`). R1, R2 and R9 are
the worst: under 1% precision on those businesses, thousands of good customers' money held.

**Eligibility** (`feat_fast_lane_exclusions`, config `fast_lane`): open at least 365 days, and no bounced check or
returned ACH debit in the last 180 days. Both are bank data; no label is used. A business can fall out and come back.

**Soften, not skip.** For a fast-lane business, R1, R2 and R9 (aimed at a fraudster's own account) act at most as an
RFI. Rules that protect a victim (R4, R5, R8) and the credit rules (R10 to R12) keep their action:
- account takeovers, payment redirection and bust-outs all target or imitate established, clean accounts;
- `fast_lane_clear_all` (every alert on a fast-lane business dropped) is graded as the cautionary version. It lets
  through takeovers, payment redirection and most bust-outs (`bt_fast_lane_typologies`).
Industry is shown in the segment table for discovery only: a handful of fraud cases per industry is too thin to set
thresholds on.

**The cap is swept, not tuned.** Softening applies below a per-alert amount (config `max_amount_sweep`: $5,000,
$10,000, $25,000, none). Two reasons it is not chosen automatically:
- Under the stated costs (ADR-008) a hold on a good customer costs only the money it ties up, so net value barely
  moves and cannot choose the cap. The number to judge is fraud let through per hold avoided: what a hold on an
  established, clean customer is worth is a business decision.
- The training months show no fraud let through at $25,000; the test months show about $200K. Choosing on the
  training months would have picked the cap that fails out of sample.
The `fast_lane:<cap>` rule sets show the whole curve.

**Decision: recommend the $10,000 cap** (`recommended_max_amount`). It lets no fraud through on either the training or
the test months, while sparing about 1,600 good customers' holds and about 490 good businesses in the test months. It
was chosen after seeing the test months, so its clean test result is not an out-of-sample confirmation; the next
quarterly review (ADR-024) is the first honest check. R1, R2 and R9 carry a `scope` entry in the change log for it.

**Onboarding approval rate** (`bt_onboarding_decline_bar`): R6's decline bar swept at 3 (today), 4, 5 and never,
on top of the challenger. The approval rate counts every application, including those the bank's existing checks
decline, which dominate it; R6's decline tier moves it by under a point.

**Caveats.** A known per-payment cap invites splitting payments under it (fraudsters did that with the instant
payout cap, ADR-021). A cap on two days' outflow would resist it; not built. The fast lane never helps a new business.
