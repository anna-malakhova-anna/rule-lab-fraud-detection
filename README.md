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
Synthetic data: 12,000 businesses, 10,688,609 transactions, 234 planted fraud cases (80 start in the held-out test months, Jan 2026 onward). Ranges are 90% bootstrap ranges over businesses.

| Test months (held out) | Champion | Challenger |
|---|---|---|
| Fraud $ prevented (90% range) | $3.86M ($2.84M to $5.02M) | $4.47M ($3.40M to $5.67M) |
| Share of fraud $ prevented | 80% (72% to 87%) | 92% (88% to 96%) |
| Fraud cases detected | 68 of 80 | 79 of 80 |
| Alerts that were fraud (precision) | 2.4% | 2.7% |
| Good businesses flagged | 3,670 | 3,826 |
| Good businesses with money held | 3,039 | 3,195 |
| Good applicants declined | 1 | 1 |
| Payrolls delayed | 0 | 0 |
| Good-customer dollar-days held | $280.49M | $285.73M |
| Reviews per business day (avg / max) | 85.9 / 186 | 88.5 / 190 |
| Days over review capacity | 49 of 129 | 52 of 129 |
<!-- results:end -->

## What's in it

- **A synthetic bank** (`generator/`): 12,000 businesses in ten industries, about 18 months of activity,
  biweekly payroll and seasonality. It includes onboarding applications (some declined), online-banking
  logins and devices, and the odd-but-legitimate businesses that create false positives: a seasonal
  landscaper, a shop taking dozens of small checks, a marketplace seller with hundreds of small transfers, a
  business that has just hired a bookkeeper.
- **A line of credit** that businesses qualify for after six months, with a limit based on what flows through
  their account. Some honest businesses fail and default on it. That's a credit loss, reported on its own line
  and never counted as fraud.
- **Seven planted fraud types**, with parameters in `config/generation.yaml` and an answer key that only the
  backtest reads:
  - check deposit fraud
  - vendor bank-detail change (BEC)
  - synthetic or shell business rings at onboarding
  - money mules
  - account takeover
  - first-party ACH return fraud, which starts in month 12 and that none of my rules were designed for
  - credit bust-out: clean history, inflows pumped up, a bigger limit, then the whole line drawn and gone
- **Twelve rules in SQL** (`dbt/models/rules/`). Thresholds are in `config/rules.yaml`, each with a one-line
  rationale and a status: running today (champion) or proposed (challenger).
- **A backtest** (`dbt/models/backtest/`) that grades every rule and rule set on fraud dollars prevented,
  good businesses flagged, good applicants declined, payrolls delayed, and reviews per day against capacity.
  It includes a threshold sweep and a champion/challenger comparison on held-out months.
- **Monitoring** (`dbt/models/monitoring/`): weekly alarms on returned payments that use no fraud labels.
  This is how the month-12 pattern was found (`docs/investigations/INV-001-ach-debit-returns.md`).
- **Risk Ops** (`dbt/models/backtest/ops/`, `scripts/queue_sim.py`): alerts become cases with a priority score.
  A queue at the team's real capacity shows what working the highest-priority cases first is worth compared with
  working the oldest first. Each rule has an analyst playbook in `docs/playbooks/`.
- **A stakeholder pack** (`docs/stakeholder/`): the current recommendation written three ways, for an executive,
  for the ops team and as an engineering ticket. The numbers are generated and the prose is a draft.
- **A results site** (`make site`, committed in `site/`): overview, trade-off curves, Risk Ops, one page per
  fraud type, monitoring, a limitations page and a glossary.
- **Decisions** are in `docs/decisions/`. **Draft rule-change memos** are in `docs/memo/`: one per phase. Earlier
  phases' numbers are frozen at the commit that produced them.

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

`make all` runs generate, load, build, backtest, results, site and test. Open `site/index.html` for the results.
