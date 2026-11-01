# Playbook: R8 New device, contact change, new payee

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `ATO_SEQUENCE` |
| Status | running (champion) |
| Action | hold |
| Fires when | hours since the first login from a device never seen on this account <= 12 |
| Why it exists | A new device, then a change to the email or phone on file, then a first payment to a payee added after that login, is the account-takeover sequence. |
| Cases per business day (test months) | 0.1 |
| Share that were fraud (test months) | 100.0% |
<!-- playbook-facts:end -->

## What to check
- Contact the owner on the phone number on file BEFORE the recent change, not the new one.
- Did the owner change their device and contact details themselves (new phone, new bookkeeper)?

## What clears the case
- The owner confirms the device, the contact change and the new payee through the old contact details.

## What escalates it
- The owner did not make the change: freeze the account and reset its credentials.

## What to ask the customer (RFI)
- Do not send an RFI to the new contact details; they may belong to the fraudster.
