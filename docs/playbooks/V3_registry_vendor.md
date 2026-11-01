# Playbook: V3 Registry check fails

<!-- playbook-facts:start -->
|  |  |
|---|---|
| Reason code | `VENDOR_REGISTRY_FAIL` |
| Status | vendor signal, graded in the vendor bake-off (module D) |
| Action | rfi |
| Fires when | Larchstone verification (90 = not found or mismatch, 10 = verified) >= 50 |
| Why it exists | A business the registry can't find, or whose details don't match, is a common sign of a shell. |
| Alerts per business day, rule alone (test months) | 0.3 |
| Share that were fraud (test months) | 27.8% |
<!-- playbook-facts:end -->

## What to check
- Larchstone's result: not found or mismatch, and which field didn't match.
- Very new and sole-trader businesses are sometimes missing from registries.

## What clears the case
- Formation documents match the application.

## What escalates it
- The applicant also shares identity with earlier applicants (R6).

## What to ask the customer (RFI)
- Formation documents and proof of business address.
