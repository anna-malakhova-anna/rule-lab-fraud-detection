# Playbook: V2 Contact vendor flags an email or phone

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `VENDOR_CONTACT_RISK` |
| Status | vendor signal, graded in the vendor bake-off (module D) |
| Action | rfi; hold when the score is >= 0 and the case is eligible |
| Fires when | Quenchwire email and phone risk score (0-100) >= 80 |
| Why it exists | An email or phone the vendor rates risky, at onboarding or on a contact change before a payment. |
| Alerts per business day, rule alone (test months) | 0.2 |
| Share that were fraud (test months) | 65.0% |
<!-- playbook-facts:end -->

## What to check
- Quenchwire's score and what changed: a new business domain is common for honest new businesses.

## What clears the case
- The owner verifies the new contact through the old one, or the domain belongs to the business.

## What escalates it
- The change came with a new device and a new payee: possible takeover (R8).

## What to ask the customer (RFI)
- Verify the email and phone through a channel the bank already trusts.
