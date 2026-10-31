# INV-001: Unauthorized ACH-debit returns

> Synthetic data. The facts table is generated from the warehouse by `make results`; the rest is my write-up
> of how I would have worked the alarm, and is a draft.

## What fired

The weekly return monitor (`monitoring.mon_return_alarms`) compares each return series, by rail and return
reason, with its own previous 12 weeks. Unauthorized returns on ACH debits had been close to zero all year.
Then they weren't.

<!-- inv-facts:start -->
| Fact (from the warehouse) | Value |
|---|---|
| Unauthorized ACH-debit returns, all weeks before the alarm | 7 |
| First alarm (week of) | 22 Dec 2025: 5 returns vs a trailing mean of 0.2 |
| Alarm visible (week closes) | 29 Dec 2025 |
| Answering rule (R9) live from | 12 Jan 2026 |
| Unauthorized ACH-debit returns after the alarm | 55 ($1.69M) |
| Share of those returned dollars no champion rule had alerted on | 31% |
| ACH return fraud cases starting in the test months | 19 |
| Prevented by the champion (no ACH rule) | $543K of $1.20M |
| Prevented by the challenger (with R9 from its live date) | $1.06M of $1.20M |
<!-- inv-facts:end -->

## What I looked at

1. **Who.** The returned debits sat on a handful of accounts, some opened only months earlier, with no link
   to each other. That isn't a ring.
2. **The money's path.** Each account pulled money in by ACH debit from external accounts it had never used
   before, then sent most of it out by wire or ACH within one to three days. The debits came back as
   unauthorized days later. The account holders, not the bank, are the fraudsters.
3. **Why the rules missed it.** R1 measures fresh money leaving fast, but only fresh *check* money. Nothing
   in the champion watches ACH debits. A few cases were touched by R5 (payment far above usual to a payee),
   but only because the money went to the owner's own account at an unusual size. That catch was luck, not
   design, and R5 only asks for documents.

## What I changed

**R9 (ACH debit money out fast)** is R1's logic on the ACH-debit rail. It looks at outbound payments made
while ACH debits pulled in during the last 5 days can still come back, and scores the share of that money
already sent out on top of a normal week of spending. I set its cutoff to R1's shipped cutoff (0.4), from
alert volumes only, before grading it. It goes live 10 business days after the alarm, and the backtest
credits it only from then (ADR-014).

## What to watch

- Unauthorized ACH-debit returns per week. These will NOT fall when R9 goes live: R9 holds the money going
  out, but the fraudulent pulls still happen and still come back. What should fall is the money already gone
  when a return arrives (the "no champion alert" column on the results page).
- R9's alerts on owners topping up their own business. Those are its main source of false positives.
