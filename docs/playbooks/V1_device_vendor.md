# Playbook: V1 Device vendor flags a device

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `VENDOR_DEVICE_RISK` |
| Status | vendor signal, graded in the vendor bake-off (module D) |
| Action | rfi; hold when the score is >= 0 and the case is eligible |
| Fires when | Tallowmere device risk score (0-100) >= 80 |
| Why it exists | A device the vendor has seen behind fraud elsewhere, at onboarding or on a new-device login before a payment. |
| Alerts per business day, rule alone (test months) | 0.4 |
| Share that were fraud (test months) | 65.3% |
<!-- playbook-facts:end -->

## What to check
- Tallowmere's score and which device: is it a bookkeeper's or an office device used by many accounts?
- At a payment: the new-device login it scored, and any contact change since.

## What clears the case
- A known shared device (bookkeeper, office) with nothing else unusual.

## What escalates it
- A high score plus a contact change or new payee: treat as possible takeover (R8).

## What to ask the customer (RFI)
- At onboarding: confirm who will use the account and from where.
