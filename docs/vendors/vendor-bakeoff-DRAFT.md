# DRAFT: Vendor bake-off: buy or build

> **DRAFT. Numbers and the buy / don't-buy line are generated from the warehouse by `make results`; the prose is
> mine to write.** The three vendors are invented, and so are their prices and accuracy (ADR-022).

## Recommendation

<!-- vendor-decisions:start -->
| Vendor | What it is | Price per call | Best call strategy | Net value (test months) | Fast enough for payments | Decision |
|---|---|---|---|---|---|---|
| Larchstone Registry Check | business registry verification (KYB) | $1.50 | Onboarding only | $19K | no | buy |
| Quenchwire Contact Signals | email and phone risk score | $0.10 | Onboarding only | $5K | yes | buy |
| Tallowmere Device Risk | device risk score | $0.05 | Every call point | $67K | yes | buy |
<!-- vendor-decisions:end -->

[One or two sentences per vendor: why buy or not, and the price at which the answer would flip.]

## The full comparison (test months)

<!-- vendor-bakeoff:start -->
| Vendor | Call strategy | Calls | Vendor cost | Fraud $ added | Cases only it caught | Extra good businesses flagged | Cost per $ prevented | Break-even price per call | Net value |
|---|---|---|---|---|---|---|---|---|---|
| Larchstone Registry Check | Onboarding only | 1,264 | $2K | $24K | 0 | 11 | $0.081 | $16.74 | $19K |
| Larchstone Registry Check | Only when already risky | 213 | $320 | $0 | 0 | 0 | $-343060512768.000 | $-0.00 | −$320 |
| Quenchwire Contact Signals | Every call point | 1,722 | $172 | $6K | 0 | 5 | $0.031 | $2.58 | $4K |
| Quenchwire Contact Signals | Onboarding only | 1,264 | $126 | $6K | 0 | 0 | $0.023 | $4.34 | $5K |
| Quenchwire Contact Signals | Only when already risky | 319 | $32 | $0 | 0 | 4 | $-34252364185.600 | $-2.63 | −$872 |
| Tallowmere Device Risk | Every call point | 4,785 | $239 | $69K | 0 | 5 | $0.003 | $14.12 | $67K |
| Tallowmere Device Risk | Onboarding only | 1,264 | $63 | $31K | 0 | 0 | $0.002 | $24.44 | $31K |
| Tallowmere Device Risk | Only when already risky | 216 | $11 | $0 | 0 | 0 | $-11596411699.200 | $-0.00 | −$11 |
<!-- vendor-bakeoff:end -->

## How to read it

[Fraud $ added is on top of today's rules; cases only it caught are cases today's rules miss entirely. The
break-even price per call is the most the vendor could charge here and still pay for itself.]
