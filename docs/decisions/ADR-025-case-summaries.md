# ADR-025: Case summaries are templates checked line by line; a language model can come later

**What.** Each case (`cases.case_records`: one business, one review day, today's and the proposed rules at their
configured cutoffs) gets a two- or three-line summary: who the business is and what it is queued for, then its
strongest one or two alerts and the evidence behind them (`scripts/case_summaries.py`). The case record is built
from bank data and the rules' own evidence only; no answer key, as an analyst has none.

**The guardrail.** Every line is one claim and ends with its citations: the case fields it rests on. `check`
rejects a line that cites nothing, cites a field the case does not have, names a rule none of its fields belongs
to, or states a number or date none of its cited fields holds at the precision written. Text copied verbatim from a
cited field (a business name, an industry) counts as traced.

**Measurement.** Template summaries cannot invent, so their error rate is zero by construction; reporting only
that would say nothing about the check. So the summaries of 500 sampled cases are corrupted in seven known ways and
the check's rejection rate is reported for each (`analysis.summary_checks`). Five are rejected every time. Two are
known limits and pass every time: an invented sentence with no numbers that cites a real field, and two cited
numbers swapped. The check proves traceability, not meaning.

**Writers.** Only `template` exists (config `config/case_summaries.yaml`): deterministic and offline, so the build
needs no API key. A language-model writer would sit behind the same interface (a case's fields in, text out), read
its key from an environment variable, and have every line held to the same check; the corruption table would be
re-run for it before it is switched on.

**What the check caught before release.**
- Template lines saying an applicant had been "open -4 days": applications are reviewed before the account opens.
  The template now says when the account would open.
- A generator bug: some existing businesses that turned to mule or deposit fraud were active months before their
  account opened, and payroll could start before the payroll sub-account opened. Fixed in `generator/world.py` and
  `generator/legit.py` (a test now checks that no transaction precedes its account's opening). This regenerated
  the world, so every reported number moved slightly; the one decision that changed is the registry vendor's
  (ADR-022 follow-up).
