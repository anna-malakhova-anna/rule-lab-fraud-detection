# ADR-011: 12,000 businesses, about 1.85% with a planted case

**Decision.** 12,000 businesses and 222 cases across six fraud types:

| Fraud type | Cases |
|---|---|
| check deposit fraud | 42 |
| BEC | 42 |
| shell businesses (7 rings) | 36 |
| mules | 42 |
| account takeover | 36 |
| ACH return fraud (month 12 on) | 24 |

Review capacity scales with the book: the same 1.5 analysts per 8,000 businesses (ADR-004) becomes 2.25
analysts, or 90 reviews per business day.

**Why.** Five fraud types at 8,000 businesses would leave about 25 cases each, and only a handful in the test
months. 12,000 keeps prevalence inside the 0.5 to 2% band and generation under a minute (about 35 seconds).

**Shell rings are spread evenly over the window** so both periods see rings. The first draw put all of them in
the tuning months.
