# Playbook: R3 Many new check payers

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CHK_NEW_PAYERS` |
| Status | running (champion) |
| Action | rfi |
| Fires when | industry z-score of distinct first-time check payers in the last 7 days >= 5 |
| Why it exists | Checks from many payers the business has never been paid by before, compared with what is normal for its industry. |
| Alerts per business day, rule alone (test months) | 20.0 |
| Share that were fraud (test months) | 1.8% |
<!-- playbook-facts:end -->

## What to check
- Compare with the industry: tutoring, lessons and community businesses take many small checks.
- Are the payers individuals paying similar small amounts, or a few large unrelated checks?

## What clears the case
- Many small checks that match the business's line of work (fees, lessons, market stall).

## What escalates it
- Large checks from unrelated businesses, followed by withdrawals.

## What to ask the customer (RFI)
- What the business sells and how its customers usually pay.
