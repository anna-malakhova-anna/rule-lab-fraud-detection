# Playbook: C1 Instant payout from a young account

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `INSTANT_NEW_ACCOUNT` |
| Status | launch control: a pre-send check on instant payouts (module C) |
| Action | delay |
| Fires when | days since the account opened <= 90 |
| Why it exists | A young account has no history to judge; it waits for standard payments until it has some. |
| Alerts per business day, rule alone (test months) | 17.3 |
| Share that were fraud (test months) | 2.2% |
<!-- playbook-facts:end -->

## What to check
- Nothing to review by default: the payout goes out the standard way automatically.
- If the customer asks, confirm the account's age and when instant payouts unlock.

## What clears the case
- The account reaches the age limit; instant payouts unlock without action.

## What escalates it
- The same payout also triggers a payment rule (R1, R7, R9, R11): work that case first.

## What to ask the customer (RFI)
- None. Explain the limit; no documents are needed.
