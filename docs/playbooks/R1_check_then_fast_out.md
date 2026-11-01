# Playbook: R1 Check money out fast

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CHK_OUT_FAST` |
| Status | running (champion) |
| Action | hold |
| Fires when | share of the last 72 hours of check deposits that left in the last 48 hours on top of a normal week of the account's spending >= 0.4 |
| Why it exists | Money leaving within hours of check deposits that have not had time to clear is how deposit fraud turns into loss. |
| Cases per business day (test months) | 29.2 |
| Share that were fraud (test months) | 1.5% |
<!-- playbook-facts:end -->

## What to check
- Were the recent checks deposited by mobile, and from payers this business has used before?
- Where did the outgoing money go: an established vendor, or a payee added in the last few days?
- Does the business have a reason for a big week (a seasonal peak, a large job)?

## What clears the case
- Checks from long-standing payers, and the money went to known vendors at their usual amounts.

## What escalates it
- Any check comes back returned while the case is open.
- Money went to a payee added within 72 hours.

## What to ask the customer (RFI)
- A copy of the invoice or contract behind the largest check.
- What the outgoing payment was for.
