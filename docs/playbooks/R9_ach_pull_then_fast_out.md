# Playbook: R9 ACH debit money out fast

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `ACH_DEBIT_OUT_FAST` |
| Status | running (champion) |
| Action | hold |
| Fires when | share of the last 5 days of ACH debits pulled in that left in the last 48 hours on top of a normal week of the account's spending >= 0.4 |
| Why it exists | Money pulled in by ACH debit and paid straight back out, above normal spending, is R1's pattern on a rail R1 never watched. |
| Cases per business day (test months) | 4.2 |
| Share that were fraud (test months) | 5.7% |
<!-- playbook-facts:end -->

## What to check
- Whose accounts were the ACH debits pulled from, and is the business authorised on them?
- Is this the owner's usual top-up from their own account, at the usual size?

## What clears the case
- A top-up from the owner's own account, in line with earlier ones.

## What escalates it
- Debits from accounts the business has never used, or any debit returned as unauthorized.

## What to ask the customer (RFI)
- Proof the business owns or is authorised on the external accounts it pulled from.
