# Playbook: R2 Check far above own baseline

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CHK_ABOVE_BASELINE` |
| Status | running (champion) |
| Action | hold |
| Fires when | deposit amount / the account's trailing 90-day average monthly inflow (stated revenue when history is under 30 days) >= 0.5 |
| Why it exists | A single check worth more than the account normally takes in over a month is out of character for that account. |
| Alerts per business day, rule alone (test months) | 16.9 |
| Share that were fraud (test months) | 1.8% |
<!-- playbook-facts:end -->

## What to check
- Is the payer a known client, and does the amount fit a job or contract the business would have?
- Is this a seasonal business at the start of its peak?

## What clears the case
- A known payer and a plausible job: for example, a contractor's progress payment.

## What escalates it
- The payer has never paid this business, and money starts leaving before the check clears.

## What to ask the customer (RFI)
- The invoice for the deposited check.
- A contact at the payer we can verify independently.
