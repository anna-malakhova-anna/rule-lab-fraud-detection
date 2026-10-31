# ADR-015: R6 declines only strong identity links

**Context.** R6 originally declined every applicant at or above its cutoff. Under the $300 decline cost
(ADR-012), tuning picked the loosest cutoff: one shared attribute. That declined good applicants whose only
link was a bookkeeper's device or a co-working address, 174 of them in the six test months. Meanwhile, the
check rules already catch most shells at their bust-out.

**Decision.** R6 has two tiers:
- **Score ≥ 3 → decline.** That means 3 or more shared attributes with one earlier applicant, or 2 shared
  attributes plus incorporation within 90 days. Ring members share device, phone, address and email domain,
  so they land here. A bookkeeper's device or a co-working address alone never does. This tier is fixed, not
  tuned.
- **Below that, down to the tuned cutoff → RFI.** Ask the applicant for documents before opening. Under
  ADR-003 an RFI prevents half the loss, and it costs a review and some friction, not a lost customer.

**Mechanism.** Any rule can now carry `escalate: {action, at}` in `config/rules.yaml`. A hit whose score also
passes `at` gets the stronger action. Live rule hits, the sweep and the champion/challenger rule sets all
apply it the same way (`hit_action` macro).
