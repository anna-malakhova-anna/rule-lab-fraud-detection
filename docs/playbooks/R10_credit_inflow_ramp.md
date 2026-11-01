# Playbook: R10 Inflows ramped before a credit decision

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `CREDIT_INFLOW_RAMP` |
| Status | proposed (challenger) |
| Action | rfi |
| Fires when | last 30 days of inflow / average month of the 90 days before that >= 3 |
| Why it exists | A line opening or limit increase asked for right after inflows jumped above the account's own history is how a bust-out earns a bigger line. |
| Alerts per business day, rule alone (test months) | 0.4 |
| Share that were fraud (test months) | 24.5% |
<!-- playbook-facts:end -->

## What to check
- Where did the recent extra inflow come from: established clients, or new outside accounts?
- Does the business have a seasonal peak that explains the ramp?

## What clears the case
- Inflows from established clients, or a seasonal business entering its usual peak.

## What escalates it
- The extra inflow came from new accounts and went straight back out (round-tripping).

## What to ask the customer (RFI)
- Recent financial statements or invoices supporting the higher revenue before granting the line or increase.
