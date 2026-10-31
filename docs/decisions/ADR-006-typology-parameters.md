# ADR-006: Fraud typologies and the odd-but-legitimate businesses

All parameters are in `config/generation.yaml`. Module docstrings describe each scheme.

**Check-deposit fraud** (`generator/typologies/check_deposit_fraud.py`). 60% of cases are accounts opened for
the scheme, which strike 20 to 90 days after opening. 40% are existing customers turning to first-party
fraud. Two variants:
- *single large:* 1 to 2 checks, each 1.5 to 8 times normal monthly inflow.
- *multi-payer:* 4 to 12 checks from payers the business has never seen, spread over a few days.

Withdrawals start a median of 10 hours after the first deposit and take 70 to 95% of the check total. Checks
come back 2 to 7 days later. Every check stays under a **$50,000 per-check mobile deposit limit**, which I
added after first-party cases at large businesses produced unrealistically big losses.

**BEC vendor change** (`generator/typologies/bec_vendor_change.py`). A vendor the business has paid at least
3 times gets its bank details changed. The next 1 to 2 payments go to the fraudster, a median of 48 hours
later. Half the cases are the vendor's normal amount (hard to see by amount), half are 1.8 to 6 times
normal. The real vendor chases payment 5 to 25 days later, the details are restored, and the invoice is paid
again.

**Odd but legitimate.** Built so false positives have realistic sources:
- seasonal-heavy landscapers
- businesses taking dozens of small checks
- lumpy contractors with big checks spent fast
- annual big invoices
- vendors that change bank details more often than most

Legitimate bank-detail changes also happen at a base rate of 3% per vendor per year.

**Known gaps (Phase 1):** no balances or overdrafts, no declined applications, no login or device events.
Those arrive with the Phase 2 typologies.
