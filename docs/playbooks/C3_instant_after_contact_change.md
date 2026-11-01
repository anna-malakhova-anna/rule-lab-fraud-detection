# Playbook: C3 Instant payout right after a contact change or new device

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `INSTANT_AFTER_CONTACT_CHANGE` |
| Status | launch control: a pre-send check on instant payouts (module C) |
| Action | delay |
| Fires when | hours since the last contact change or new-device login <= 72 |
| Why it exists | Right after a new device or a change of email or phone is when a taken-over account pays out. |
| Alerts per business day, rule alone (test months) | 2.2 |
| Share that were fraud (test months) | 6.1% |
<!-- playbook-facts:end -->

## What to check
- Was the email, phone or device change made by the owner? Use the contact details from BEFORE the change.

## What clears the case
- The owner confirms the change through the old contact details.

## What escalates it
- The owner didn't make the change: freeze the account and reset its credentials (R8 playbook).

## What to ask the customer (RFI)
- Do not send it to the new contact details.
