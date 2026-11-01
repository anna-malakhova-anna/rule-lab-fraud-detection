# Playbook: R12 Line drawn to limit soon after increase

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CREDIT_FULL_DRAW` |
| Status | proposed (challenger) |
| Action | hold |
| Fires when | days since the limit was last raised <= 14 |
| Why it exists | Drawing the line to its limit days after it was raised is the bust-out's signature. |
| Alerts per business day, rule alone (test months) | 0.2 |
| Share that were fraud (test months) | 100.0% |
<!-- playbook-facts:end -->

## What to check
- Why did the business need the whole line so soon after the increase?
- Did inflows ramp up just before the increase (see R10)?

## What clears the case
- A documented large purchase the increase was granted for.

## What escalates it
- The draw goes out to a new external account, or the account goes quiet after the draw.

## What to ask the customer (RFI)
- What the drawn money is for, and the supporting invoice.
