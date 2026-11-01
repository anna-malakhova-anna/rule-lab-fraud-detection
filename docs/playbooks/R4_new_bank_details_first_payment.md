# Playbook: R4 First payment to changed bank details

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `PAYEE_DETAILS_CHANGED` |
| Status | running (champion) |
| Action | hold |
| Fires when | days since the payee's bank details were changed <= 7 |
| Why it exists | The first payment to a known payee's newly changed bank details is the moment a vendor-impersonation scam pays out. |
| Alerts per business day, rule alone (test months) | 1.7 |
| Share that were fraud (test months) | 2.2% |
<!-- playbook-facts:end -->

## What to check
- When and how were the vendor's bank details changed, and by whom?
- Has the business confirmed the change with the vendor by a phone number already on file?

## What clears the case
- The vendor confirms the new details through a known contact.

## What escalates it
- The change request came by email only, or the vendor cannot be reached on the number on file.

## What to ask the customer (RFI)
- Ask the customer to call the vendor on a number they already had (not one from the email) and confirm the change.
