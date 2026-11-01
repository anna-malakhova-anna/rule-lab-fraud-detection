# Playbook: R7 Many new senders, swept out

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `MULE_FAN_IN` |
| Status | running (champion) |
| Action | hold |
| Fires when | distinct first-time senders of ACH or wire payments in the last 14 days >= 5 |
| Why it exists | Many first-time senders paying in, and most of it paid straight back out, is how a mule account moves scam proceeds. |
| Alerts per business day, rule alone (test months) | 5.0 |
| Share that were fraud (test months) | 21.3% |
<!-- playbook-facts:end -->

## What to check
- Who are the senders: customers of the business, or individuals with no link to what it sells?
- Where does the swept money go, and how quickly?

## What clears the case
- A marketplace or event business whose customers pay small amounts, swept weekly to the owner.

## What escalates it
- Senders' banks send recall requests, or the money goes to new external accounts within a day.

## What to ask the customer (RFI)
- What the incoming payments are for, with a few example invoices or orders.
