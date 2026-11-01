# DRAFT: Vendor bake-off: buy or build

> **DRAFT. Numbers and the buy / don't-buy line are generated from the warehouse by `make results`; the prose is
> mine to write.** The three vendors are invented, and so are their prices and accuracy (ADR-022).

## Recommendation

<!-- vendor-decisions:start -->
| Vendor | What it is | Price per call | Best call strategy | Net value (test months) | Cases behind it | Fast enough for payments | Decision |
|---|---|---|---|---|---|---|---|
| Larchstone Registry Check | business registry verification (KYB) | $1.50 | Only when already risky | −$318 | 0 | no | don't buy |
| Quenchwire Contact Signals | email and phone risk score | $0.10 | Onboarding only | $14K | 2 | yes | buy |
| Tallowmere Device Risk | device risk score | $0.05 | Every call point | $45K | 3 | yes | buy |
<!-- vendor-decisions:end -->

[One or two sentences per vendor: why buy or not, and the price at which the answer would flip.]

## The full comparison (test months)

<!-- vendor-bakeoff:start -->
| Vendor | Call strategy | Calls | Vendor cost | Fraud $ added | Cases behind it | Cases only it caught | Extra good businesses flagged | Cost per $ prevented | Break-even price per call | Net value |
|---|---|---|---|---|---|---|---|---|---|---|
| Larchstone Registry Check | Onboarding only | 1,263 | $2K | $3K | 1 | 0 | 13 | $0.558 | $0.55 | −$1K |
| Larchstone Registry Check | Only when already risky | 212 | $318 | $0 | 0 | 0 | 0 | n/a | $0.00 | −$318 |
| Quenchwire Contact Signals | Every call point | 1,719 | $172 | $15K | 2 | 0 | 3 | $0.012 | $8.11 | $14K |
| Quenchwire Contact Signals | Onboarding only | 1,263 | $126 | $15K | 2 | 0 | 0 | $0.009 | $11.52 | $14K |
| Quenchwire Contact Signals | Only when already risky | 316 | $32 | $0 | 0 | 0 | 2 | n/a | −$1.33 | −$452 |
| Tallowmere Device Risk | Every call point | 4,783 | $239 | $46K | 3 | 0 | 5 | $0.005 | $9.41 | $45K |
| Tallowmere Device Risk | Onboarding only | 1,263 | $63 | $0 | 0 | 0 | 0 | n/a | −$0.07 | −$153 |
| Tallowmere Device Risk | Only when already risky | 215 | $11 | $0 | 0 | 0 | 0 | n/a | $0.00 | −$11 |
<!-- vendor-bakeoff:end -->

## How to read it

[Fraud $ added is on top of today's rules; cases only it caught are cases today's rules miss entirely. The
break-even price per call is the most the vendor could charge here and still pay for itself.]
