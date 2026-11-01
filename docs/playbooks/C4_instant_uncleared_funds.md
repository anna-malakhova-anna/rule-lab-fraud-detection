# Playbook: C4 Instant payout funded by money that can still come back

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `INSTANT_UNCLEARED_FUNDS` |
| Status | launch control: a pre-send check on instant payouts (module C) |
| Action | delay |
| Fires when | returnable money received in the last few days / the payout amount >= 0.5 |
| Why it exists | Instant payouts must not spend money that can still come back (checks, ACH debits, fresh line draws). |
| Alerts per business day, rule alone (test months) | 82.9 |
| Share that were fraud (test months) | 1.5% |
<!-- playbook-facts:end -->

## What to check
- Which recent deposits fund the payout: checks, ACH debits pulled in, or a credit-line draw?

## What clears the case
- The deposits clear; the money becomes eligible for instant payouts.

## What escalates it
- A funding deposit is returned while the payout is pending, or a payment rule flags the same money.

## What to ask the customer (RFI)
- None by default. If the customer needs it sooner: evidence the deposits are good (e.g. the client's remittance).
