# Playbook: R11 Credit draw money out fast

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CREDIT_DRAW_OUT_FAST` |
| Status | proposed (challenger) |
| Action | hold |
| Fires when | share of the last 72 hours of line draws that left in the last 48 hours on top of a normal week of the account's spending >= 0.3 |
| Why it exists | Money drawn on the line and sent straight back out, above normal spending, is the moment a bust-out cashes out. |
| Cases per business day (test months) | 2.4 |
| Share that were fraud (test months) | 7.4% |
<!-- playbook-facts:end -->

## What to check
- What was the drawn money spent on: payroll and suppliers, or a transfer to a new external account?

## What clears the case
- The draw paid for normal operating costs.

## What escalates it
- The draw left for a new external payee within hours. Freeze further draws.

## What to ask the customer (RFI)
- What the transferred money was for, with the invoice.
