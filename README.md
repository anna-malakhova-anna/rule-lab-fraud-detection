# SMB Fraud Rule Lab

**Which fraud rules should a small-business bank run, at what thresholds, and what does each change cost and save?**

> **All data here is synthetic.** The bank (Bramblewick Business Banking), its customers and every transaction
> are generated from a fixed seed. The fraud is planted, with an answer key. No number in this repo is a
> real-world fraud rate, loss figure or benchmark.

I'm curious about fraud at small-business neobanks, where a bad call can stop real fraud or bounce a real
company's payroll. I wanted to see that trade-off with numbers: fraud caught, good customers hurt, and how much
work the alerts create for a small review team. Since no real data is available to me, I built a bank where
I know the truth.

## Headline

<!-- results:start -->
Synthetic data: 12,000 businesses, 10,712,353 transactions, 222 planted fraud cases (71 start in the held-out test months, Jan 2026 onward). Ranges are 90% bootstrap ranges over businesses.

| Test months (held out) | Champion | Challenger |
|---|---|---|
| Fraud $ prevented (90% range) | $2.30M ($1.45M to $3.26M) | $3.96M ($2.94M to $5.14M) |
| Share of fraud $ prevented | 55% (43% to 66%) | 95% (92% to 97%) |
| Fraud cases detected | 42 of 71 | 66 of 71 |
| Alerts that were fraud (precision) | 1.5% | 3.5% |
| Good businesses flagged | 3,487 | 3,740 |
| Good businesses with money held | 2,965 | 3,122 |
| Good applicants declined | 0 | 0 |
| Payrolls delayed | 0 | 0 |
| Good-customer dollar-days held | $269.91M | $289.11M |
| Reviews per business day (avg / max) | 79.2 / 171 | 88.2 / 187 |
| Days over review capacity | 34 of 129 | 51 of 129 |
<!-- results:end -->

## What's in it

- **A synthetic bank** (`generator/`): 12,000 businesses in ten industries, about 18 months of activity,
  biweekly payroll and seasonality. It includes onboarding applications (some declined), online-banking
  logins and devices, and the odd-but-legitimate businesses that create false positives: a seasonal
  landscaper, a shop taking dozens of small checks, a marketplace seller with hundreds of small transfers, a
  business that has just hired a bookkeeper.
- **Six planted fraud types**, with parameters in `config/generation.yaml` and an answer key that only the
  backtest reads:
  - check deposit fraud
  - vendor bank-detail change (BEC)
  - synthetic or shell business rings at onboarding
  - money mules
  - account takeover
  - first-party ACH return fraud, which starts in month 12 and that none of my rules were designed for
- **Nine rules in SQL** (`dbt/models/rules/`). Thresholds are in `config/rules.yaml`, each with a one-line
  rationale and a status: running today (champion) or proposed (challenger).
- **A backtest** (`dbt/models/backtest/`) that grades every rule and rule set on fraud dollars prevented,
  good businesses flagged, good applicants declined, payrolls delayed, and reviews per day against capacity.
  It includes a threshold sweep and a champion/challenger comparison on held-out months.
- **Monitoring** (`dbt/models/monitoring/`): weekly alarms on returned payments that use no fraud labels.
  This is how the month-12 pattern was found (`docs/investigations/INV-001-ach-debit-returns.md`).
- **Decisions** are in `docs/decisions/`. **Draft rule-change memos** are in `docs/memo/`. The Phase 1
  memo's numbers are frozen from the Phase 1 build.

## How I set it up so the numbers mean something

- **Tune on one period, grade on another.** I tune new cutoffs on months 1 to 12 and compare champion with
  challenger only on months 13 to 18.
- **Tune on the labels I would actually have had.** Fraud takes time to confirm: days for a returned check,
  months for a mule, and some cases never. Tuning only sees the cases confirmed by the end of month 12.
- **The rules can't see the answer key.** A check walks dbt's lineage and fails the build if anything
  outside `models/backtest/` depends on it.
- **A new pattern has to be found, not stumbled on.** The rule for the month-12 pattern only counts from the
  day monitoring raised the alarm, plus the time an investigation takes.
- **Thresholds can't fix a rule that looks at the wrong payments.** R1 held good payrolls at every cutoff,
  so payroll is out of its scope (ADR-009).
- **Small samples get ranges.** Each fraud type has only a handful of cases in the test months.

## Limitations

Synthetic data flatters rules: I wrote the fraud, so I know its shape, and real fraud adapts once it gets
caught. Labels are delayed and sometimes missing when tuning, but the final grade still uses the full answer
key, which a real bank never gets. Costs used to choose the challenger are stated assumptions in
`config/backtest.yaml`, not measurements.

## Run it

Needs [uv](https://docs.astral.sh/uv/). Everything takes about three minutes.

```bash
make setup
make all
```

`make all` runs generate, load, build, backtest, results, site and test. The results page is written to
`site/index.html`.
