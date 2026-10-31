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
Synthetic data: 8,000 businesses, 6,933,736 transactions, 96 planted fraud cases (27 start in the held-out test months, Jan 2026 onward). Ranges are 90% bootstrap ranges over businesses.

| Test months (held out) | Champion | Challenger |
|---|---|---|
| Fraud $ prevented (90% range) | $985K ($475K to $1.58M) | $1.03M ($527K to $1.63M) |
| Share of fraud $ prevented | 82% (63% to 95%) | 86% (73% to 95%) |
| Fraud cases detected | 20 of 27 | 23 of 27 |
| Alerts that were fraud (precision) | 0.9% | 1.0% |
| Good businesses flagged | 2,302 | 2,327 |
| Good businesses with money held | 1,788 | 1,967 |
| Payrolls delayed | 999 | 0 |
| Good-customer dollar-days held | $141.73M | $177.26M |
| Reviews per business day (avg / max) | 52.3 / 126 | 51.7 / 108 |
| Days over review capacity | 33 of 129 | 39 of 129 |
<!-- results:end -->

## What's in it

- **A synthetic bank** (`generator/`): 8,000 businesses across ten industries, about 18 months of
  activity, biweekly payroll, seasonality, and the odd-but-legitimate businesses that create false positives
  (a seasonal landscaper, a shop that takes dozens of small checks, a contractor with big lumpy checks).
- **Two planted fraud types** in Phase 1: mobile check deposit fraud and business email compromise
  (a vendor's bank details changed, then the business pays the fraudster). Parameters are in
  `config/generation.yaml`. The answer key is written separately and only the backtest reads it.
- **Five rules in SQL** (`dbt/models/rules/`). Thresholds live in `config/rules.yaml`, each with a
  one-line rationale.
- **A backtest** (`dbt/models/backtest/`) that grades every rule and rule set on fraud dollars prevented,
  good businesses flagged, payrolls delayed, and reviews per day against capacity. It includes a threshold
  sweep and a champion/challenger comparison on held-out months.
- **Decisions** are in `docs/decisions/`. A **draft rule-change memo** is in `docs/memo/`.

## How I set it up so the numbers mean something

- **Tune on one period, grade on another.** I tune challenger thresholds on months 1 to 12 and compare
  champion with challenger only on months 13 to 18. Tuning and grading on the same months would flatter the
  challenger.
- **The rules can't see the answer key.** A check walks dbt's lineage and fails the build if anything
  outside `models/backtest/` depends on it.
- **Champion thresholds were set before grading.** I looked at alert volumes (which need no labels), not at
  fraud caught.
- **Thresholds can't fix a rule that looks at the wrong payments.** R1 held good payrolls at every cutoff,
  so the challenger also excludes payroll from R1 (ADR-009). The champion keeps R1 as written, so the
  difference is visible.
- **Small samples get ranges.** The test months hold only a couple dozen fraud cases, so headline numbers
  carry bootstrap ranges.

## Limitations

Synthetic data flatters rules: I wrote the fraud, so I know its shape, and real fraud adapts once it gets
caught. Labels here are complete and arrive instantly; in reality they arrive late and incomplete (modelling
that delay is planned for a later phase). Costs used to choose the challenger are stated assumptions in
`config/backtest.yaml`, not measurements.

## Run it

Needs [uv](https://docs.astral.sh/uv/). Everything takes about two minutes.

```bash
make setup
make all
```

`make all` runs generate, load, build, backtest, results, site and test. The results page is written to
`site/index.html`.
