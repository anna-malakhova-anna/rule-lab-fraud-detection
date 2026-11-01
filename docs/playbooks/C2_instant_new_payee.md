# Playbook: C2 Instant payout to a new or changed payee

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `INSTANT_NEW_PAYEE` |
| Status | launch control: a pre-send check on instant payouts (module C) |
| Action | delay |
| Fires when | hours since the payee was added or its bank details last changed <= 72 |
| Why it exists | Cash-outs go to payees added or changed hours earlier; a cooling-off period gives the payment rules time. |
| Alerts per business day, rule alone (test months) | 1.3 |
| Share that were fraud (test months) | 81.0% |
<!-- playbook-facts:end -->

## What to check
- When the payee was added or its bank details changed, and from which device.
- Whether a payment rule (R4, R8) also flagged the business.

## What clears the case
- The cooling-off period passes; the payee becomes eligible for instant payouts.

## What escalates it
- The payee was added right after a new-device login or a contact change: treat as possible takeover (see R8).

## What to ask the customer (RFI)
- If the customer needs it sooner: confirm the payee through a contact already on file.
