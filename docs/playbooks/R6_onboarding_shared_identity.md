# Playbook: R6 Applicant shares identity with others

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `APP_SHARED_IDENTITY` |
| Status | running (champion) |
| Action | rfi; block when the score is >= 3 and the case is eligible |
| Fires when | most identity attributes (device, phone, address, business email domain) shared with any one earlier application, plus 1 if incorporated within young_incorporation_days >= 1 |
| Why it exists | Applicants who share a device, phone, address or business email domain with earlier applicants, and are freshly incorporated, look like a ring of synthetic businesses. |
| Alerts per business day, rule alone (test months) | 1.5 |
| Share that were fraud (test months) | 6.3% |
<!-- playbook-facts:end -->

## What to check
- Which attributes are shared, and with whom: the same owner's other business, a bookkeeper, a co-working address?
- How recently was the business incorporated, and does its stated revenue fit its age?

## What clears the case
- The link is the same owner's established second business, or a known bookkeeper or co-working space.

## What escalates it
- The linked applicants were declined, or several new businesses share device, phone and address.

## What to ask the customer (RFI)
- Proof of business address and ownership.
- How the business expects to be funded in its first month.
