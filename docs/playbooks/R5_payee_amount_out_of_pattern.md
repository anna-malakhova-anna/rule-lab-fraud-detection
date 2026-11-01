# Playbook: R5 Payment far above usual for payee

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `PAYEE_AMOUNT_OUTLIER` |
| Status | running (champion) |
| Action | rfi |
| Fires when | amount / median of the last 6 payments to the same payee >= 4 |
| Why it exists | A payment far above what this business usually pays this payee suggests an altered or fake invoice. |
| Alerts per business day, rule alone (test months) | 30.7 |
| Share that were fraud (test months) | 0.6% |
<!-- playbook-facts:end -->

## What to check
- Is there a known reason for the bigger payment: an annual invoice, equipment, a deposit?
- Did the payee's bank details change recently (see R4)?

## What clears the case
- A documented one-off invoice from an established payee with unchanged bank details.

## What escalates it
- Bank details changed recently, or the money is going to the owner's own account at an unusual size.

## What to ask the customer (RFI)
- The invoice for this payment.
