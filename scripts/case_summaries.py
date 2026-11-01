"""Case summaries for analysts, with a citation guardrail (module G, ADR-025).

Each case (cases.case_records: one business, one review day) gets a two- or three-line summary: who the business
is and what it is queued for, then the strongest one or two alerts and the evidence behind them.

The guardrail. Every line is one claim and must end with its citations: the case fields it rests on, in brackets,
for example `[alerts[0].amount, alerts[0].evidence.normal_week_outflow]`. `check` rejects a line that
  - cites nothing, or cites a field the case does not have;
  - names a rule (R1, C2, ...) that none of its cited fields belongs to;
  - states a date or a number (amounts, percentages, counts) that none of its cited fields holds, at the precision
    written, with each cited value backing at most one number.
It cannot judge meaning: a sentence with valid citations and no numbers passes whatever it says, and two cited
numbers swapped still match. The measurement reports those limits instead of hiding them.

Writers. `template` is deterministic and offline. A language-model writer can be added to WRITERS later with the
same signature (a case's fields in, summary text out); it would read its key from an environment variable, and its
output would be held to the same check. Nothing here calls a network.

Measurement. Template summaries are checked for every case (they should never fail). Then, on a sample, each
summary is corrupted in known ways and the check's catch rate is reported per kind of corruption.

Reads cases.case_records only (no answer key). Writes analysis.case_summaries and analysis.summary_checks.

  uv run python -m scripts.case_summaries
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable

import numpy as np

from scripts.common import connect, load_yaml

Fields = dict[str, object]

# ---------------------------------------------------------------------------------------------------------------
# A case as citable fields


def case_fields(row: dict) -> Fields:
    """Flatten a case record into the field paths a summary may cite."""
    f: Fields = {
        "case.action": row["action"],
        "case.alert_count": len(row["alerts"]),
        "business.legal_name": row["legal_name"],
        "business.industry": row["industry"],
        "business.open_date": row["open_date"].isoformat(),
        "business.tenure_days": row["tenure_days"],
        "business.stated_monthly_revenue": row["stated_monthly_revenue"],
    }
    for i, a in enumerate(row["alerts"]):
        for k in ("rule_id", "reason_code", "action", "txn_type", "amount", "score"):
            f[f"alerts[{i}].{k}"] = a[k]
        evidence = json.loads(a["evidence"]) if isinstance(a["evidence"], str) else a["evidence"]
        for k, v in evidence.items():
            f[f"alerts[{i}].evidence.{k}"] = v
    return f


# ---------------------------------------------------------------------------------------------------------------
# The template writer


def money(x: float) -> str:
    return f"${x:,.0f}"


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def line(text: str, *cites: str) -> str:
    return f"{text} [{', '.join(cites)}]"


ACTION_WORDS = {"hold": "a hold", "rfi": "a document request", "block": "a decline"}
TXN_WORDS = {"wire_out": "wire", "ach_out": "ACH payment", "instant_payout": "instant payout", "payroll": "payroll run",
             "check_deposit": "check deposit", "application": "application", "loc_draw": "line draw"}


def _alert_line(f: Fields, i: int) -> str | None:
    """One claim for alert i: the rule and the evidence it fired on. None if a field the template needs is missing."""
    a, e = f"alerts[{i}]", f"alerts[{i}].evidence"
    rule = str(f[f"{a}.rule_id"])
    code = rule.split("_", 1)[0]

    def v(key: str):
        return f.get(f"{e}.{key}")

    if code in ("R1", "R9", "R11"):
        source = {"R1": ("checks_prior_72h", "of check deposits"), "R9": ("ach_debits_prior_5d", "pulled in by ACH debit"),
                  "R11": ("line_draws_prior_72h", "drawn on the credit line")}[code]
        if None in (v("out_48h_incl_this"), v("normal_week_outflow"), v(source[0])):
            return None
        return line(f"{code}: {money(v('out_48h_incl_this'))} went out in two days against a normal week of "
                    f"{money(v('normal_week_outflow'))}, right after {money(v(source[0]))} {source[1]}",
                    f"{a}.rule_id", f"{e}.out_48h_incl_this", f"{e}.normal_week_outflow", f"{e}.{source[0]}")
    if code == "R2":
        if None in (v("amount"), v("reference_monthly_inflow"), v("uses_stated_revenue")):
            return None
        base = "its stated monthly revenue" if v("uses_stated_revenue") else "its usual monthly inflow"
        return line(f"R2: a {money(v('amount'))} check against {base} of {money(v('reference_monthly_inflow'))}",
                    f"{a}.rule_id", f"{e}.amount", f"{e}.reference_monthly_inflow", f"{e}.uses_stated_revenue")
    if code == "R3":
        if None in (v("new_payers_7d"), v("industry"), v("new_payers_7d_industry_z")):
            return None
        return line(f"R3: {v('new_payers_7d')} first-time check payers in a week, far above what is normal in "
                    f"{v('industry')} (z-score {v('new_payers_7d_industry_z'):.1f})",
                    f"{a}.rule_id", f"{e}.new_payers_7d", f"{e}.industry", f"{e}.new_payers_7d_industry_z")
    if code == "R4":
        if None in (v("amount"), v("days_since_bank_details_change")):
            return None
        usual = f" (usually {money(v('payee_median_last6'))})" if v("payee_median_last6") is not None else ""
        cites = [f"{a}.rule_id", f"{e}.amount", f"{e}.days_since_bank_details_change"]
        if usual:
            cites.append(f"{e}.payee_median_last6")
        return line(f"R4: first payment, {money(v('amount'))}{usual}, to a payee whose bank details changed "
                    f"{v('days_since_bank_details_change'):.1f} days earlier", *cites)
    if code == "R5":
        if None in (v("amount"), v("payee_median_last6"), v("prior_payments_to_payee")):
            return None
        return line(f"R5: {money(v('amount'))} to a payee usually paid {money(v('payee_median_last6'))}, after "
                    f"{v('prior_payments_to_payee')} earlier payments",
                    f"{a}.rule_id", f"{e}.amount", f"{e}.payee_median_last6", f"{e}.prior_payments_to_payee")
    if code == "R6":
        if None in (v("linked_applications"), v("linked_declined_applications"), v("days_incorporated")):
            return None
        shared = v("most_shared_attributes") or "nothing"
        return line(f"R6: the application shares {shared} with an earlier applicant; "
                    f"{v('linked_applications')} linked applications, {v('linked_declined_applications')} of them "
                    f"declined; incorporated {v('days_incorporated')} days before applying",
                    f"{a}.rule_id", f"{e}.most_shared_attributes", f"{e}.linked_applications",
                    f"{e}.linked_declined_applications", f"{e}.days_incorporated")
    if code == "R7":
        if None in (v("new_senders_14d"), v("new_sender_inbound_14d"), v("out_14d_incl_this")):
            return None
        return line(f"R7: {v('new_senders_14d')} first-time senders paid in {money(v('new_sender_inbound_14d'))} "
                    f"over two weeks, and {money(v('out_14d_incl_this'))} went back out",
                    f"{a}.rule_id", f"{e}.new_senders_14d", f"{e}.new_sender_inbound_14d", f"{e}.out_14d_incl_this")
    if code == "R8":
        if None in (v("hours_since_new_device"), v("contact_changes_since_new_device")):
            return None
        return line(f"R8: first payment to a payee added after a login from a new device "
                    f"{v('hours_since_new_device'):.1f} hours earlier, with {v('contact_changes_since_new_device')} "
                    f"contact change(s) since",
                    f"{a}.rule_id", f"{e}.hours_since_new_device", f"{e}.contact_changes_since_new_device")
    if code == "R10":
        if None in (v("inflow_last_30d"), v("baseline_monthly_inflow_31_120d"), v("share_last_30d_from_new_payers")):
            return None
        return line(f"R10: a credit request after {money(v('inflow_last_30d'))} came in over the last month, against "
                    f"{money(v('baseline_monthly_inflow_31_120d'))} a month before; "
                    f"{pct(v('share_last_30d_from_new_payers'))} of it from new payers",
                    f"{a}.rule_id", f"{e}.inflow_last_30d", f"{e}.baseline_monthly_inflow_31_120d",
                    f"{e}.share_last_30d_from_new_payers")
    if code == "R12":
        if None in (v("amount"), v("utilisation_after"), v("current_limit"), v("days_since_limit_increase")):
            return None
        return line(f"R12: a {money(v('amount'))} draw takes the line to {pct(v('utilisation_after'))} of its "
                    f"{money(v('current_limit'))} limit, raised {v('days_since_limit_increase'):.1f} days ago",
                    f"{a}.rule_id", f"{e}.amount", f"{e}.utilisation_after", f"{e}.current_limit",
                    f"{e}.days_since_limit_increase")
    return None


TEMPLATE_RULES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12")


def _generic_line(f: Fields, i: int) -> str:
    """For a rule without its own template: its score, which every alert has."""
    a = f"alerts[{i}]"
    code = str(f[f"{a}.rule_id"]).split("_", 1)[0]
    return line(f"{code}: scored {f[f'{a}.score']:.2f} on its own measure", f"{a}.rule_id", f"{a}.score")


def template_summary(f: Fields) -> str:
    """Headline, then the first alert of each of the two strongest rules (alerts are ordered strongest first)."""
    n = int(f["case.alert_count"])
    plural = "alert" if n == 1 else "alerts"
    action = ACTION_WORDS.get(str(f["case.action"]), f["case.action"])
    if int(f["business.tenure_days"]) >= 0:
        who = line(f"{f['business.legal_name']} ({f['business.industry']}, open {f['business.tenure_days']} days) "
                   f"is queued for {action} on {n} {plural}",
                   "business.legal_name", "business.industry", "business.tenure_days", "case.action", "case.alert_count")
    else:
        # An application, reviewed before the account opens.
        who = line(f"{f['business.legal_name']} ({f['business.industry']}), an applicant whose account would open "
                   f"{f['business.open_date']}, is queued for {action} on {n} {plural}",
                   "business.legal_name", "business.industry", "business.open_date", "case.action", "case.alert_count")
    lines = [who]
    seen: set[str] = set()
    for i in range(n):
        rule = str(f[f"alerts[{i}].rule_id"])
        if rule in seen:
            continue
        seen.add(rule)
        lines.append(_alert_line(f, i) or _generic_line(f, i))
        if len(lines) == 3:
            break
    return "\n".join(lines)


WRITERS: dict[str, Callable[[Fields], str]] = {"template": template_summary}

# ---------------------------------------------------------------------------------------------------------------
# The guardrail

CITATIONS = re.compile(r"\s\[((?:[^\[\]]|\[\d+\])+)\]\s*$")  # field paths may hold an index: alerts[0]
RULE_REF = re.compile(r"\b([RCV]\d+)\b")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER = re.compile(r"(?<![\w-])-?\$?\d[\d,]*(?:\.\d+)?%?")


def _number_matches(token: str, v: object) -> bool:
    """Does a written number equal this cited value, at the precision it is written?"""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    is_pct = token.endswith("%")
    digits = token.lstrip("-").strip("$%").replace(",", "")
    written = -float(digits) if token.startswith("-") else float(digits)
    decimals = len(digits.split(".")[1]) if "." in digits else 0
    x = 100 * v if is_pct else v
    return abs(round(x, decimals) - written) < 0.5 * 10 ** -decimals


def _unmatched_numbers(tokens: list[str], values: list[object]) -> list[str]:
    """Numbers left over when each written number must be backed by a DIFFERENT cited value. One value can't vouch
    for two numbers: a cited 9.9 must not also excuse a written 10 elsewhere in the line. Lines hold a handful of
    numbers, so trying every assignment is cheap."""
    def assign(i: int, used: frozenset) -> list[str] | None:
        if i == len(tokens):
            return []
        for j, v in enumerate(values):
            if j not in used and _number_matches(tokens[i], v):
                rest = assign(i + 1, used | {j})
                if rest == []:
                    return []
        return None

    if assign(0, frozenset()) == []:
        return []
    # Report the numbers no cited value backs on its own, or the whole line's numbers if they only fail together.
    alone = [t for t in tokens if not any(_number_matches(t, v) for v in values)]
    return alone or tokens


def check(summary: str, f: Fields) -> list[str]:
    """Problems with a summary against its case; an empty list means every claim traces to a cited field."""
    problems = []
    for text in (t for t in summary.splitlines() if t.strip()):
        m = CITATIONS.search(text)
        if not m:
            problems.append(f"no citation: {text!r}")
            continue
        paths = [p.strip() for p in m.group(1).split(",")]
        missing = [p for p in paths if p not in f]
        if missing:
            problems.append(f"cites fields the case does not have {missing}: {text!r}")
            continue
        claim, values = text[:m.start()], [f[p] for p in paths]
        # Text copied verbatim from a cited field (a business name, an industry) is traceable as it stands.
        for v in values:
            if isinstance(v, str) and v:
                claim = claim.replace(v, " ")
        for code in RULE_REF.findall(claim):
            if not any(isinstance(v, str) and v.startswith(code + "_") for v in values):
                problems.append(f"names {code}, which no cited field belongs to: {text!r}")
        claim = RULE_REF.sub("", claim)
        for d in DATE.findall(claim):
            if d not in values:
                problems.append(f"date {d} is not in a cited field: {text!r}")
        for token in _unmatched_numbers(NUMBER.findall(DATE.sub("", claim)), values):
            problems.append(f"{token} is not in a cited field: {text!r}")
    return problems


# ---------------------------------------------------------------------------------------------------------------
# Measuring the guardrail: known corruptions, and whether the check catches them

INVENTED = "The owner was reported for fraud at another bank last year"


def _alert_lines(lines: list[str], min_numbers: int = 0) -> list[int]:
    """Lines about an alert (they start with a rule code), with at least min_numbers numbers in the claim."""
    return [k for k, t in enumerate(lines)
            if RULE_REF.match(t) and len(NUMBER.findall(RULE_REF.sub("", t.rsplit(" [", 1)[0]))) >= min_numbers]


def _change_number(lines, f, rng):
    if not _alert_lines(lines, 1):
        return None
    k = int(rng.choice(_alert_lines(lines, 1)))
    claim, cites = lines[k].rsplit(" [", 1)
    tokens = list(NUMBER.finditer(RULE_REF.sub(lambda m: "_" * len(m.group()), claim)))
    t = tokens[int(rng.integers(len(tokens)))]
    old = t.group()
    digits = old.strip("$%").replace(",", "")
    new_value = float(digits) * 1.37 + 3
    new = f"{new_value:,.{len(digits.split('.')[1]) if '.' in digits else 0}f}"
    new = ("$" if old.startswith("$") else "") + (new if "," in old else new.replace(",", "")) + ("%" if old.endswith("%") else "")
    lines[k] = claim[:t.start()] + new + claim[t.end():] + " [" + cites
    return lines


def _drop_citation(lines, f, rng):
    k = int(rng.choice(_alert_lines(lines)))
    lines[k] = CITATIONS.sub("", lines[k])
    return lines


def _cite_missing_field(lines, f, rng):
    k = int(rng.choice(_alert_lines(lines)))
    lines[k] = lines[k][:-1] + ", alerts[0].evidence.prior_fraud_reports]"
    return lines


def _wrong_rule(lines, f, rng):
    k = int(rng.choice(_alert_lines(lines)))
    present = {str(v).split("_", 1)[0] for p, v in f.items() if p.endswith(".rule_id")}
    other = next(r for r in TEMPLATE_RULES if r not in present)
    lines[k] = RULE_REF.sub(other, lines[k], count=1)
    return lines


def _invented_uncited(lines, f, rng):
    return lines + [INVENTED]


def _invented_cited(lines, f, rng):
    return lines + [line(INVENTED, "business.industry")]


def _swap_numbers(lines, f, rng):
    if not _alert_lines(lines, 2):
        return None
    k = int(rng.choice(_alert_lines(lines, 2)))
    claim, cites = lines[k].rsplit(" [", 1)
    masked = RULE_REF.sub(lambda m: "_" * len(m.group()), claim)
    a, b = list(NUMBER.finditer(masked))[:2]
    lines[k] = (claim[:a.start()] + b.group() + claim[a.end():b.start()] + a.group() + claim[b.end():] + " [" + cites)
    return lines


# (name, corruption, whether the check is designed to catch it)
CORRUPTIONS = [
    ("changed a number", _change_number, True),
    ("dropped a citation", _drop_citation, True),
    ("cited a field the case does not have", _cite_missing_field, True),
    ("named the wrong rule", _wrong_rule, True),
    ("added an invented claim, uncited", _invented_uncited, True),
    ("added an invented claim with a real citation", _invented_cited, False),
    ("swapped two cited numbers", _swap_numbers, False),
]


def measure(cases: list[tuple[str, Fields, str]], rng: np.random.Generator) -> list[tuple]:
    """Catch rate of the check per corruption, on the summaries given. A corruption that does not apply to a
    summary (no number to change, say) skips it."""
    rows = []
    for name, corrupt, designed in CORRUPTIONS:
        applied = caught = 0
        for _case_id, f, summary in cases:
            lines = summary.splitlines()
            if not _alert_lines(lines):
                continue
            bad = corrupt(list(lines), f, rng)
            if bad is None:
                continue
            applied += 1
            caught += bool(check("\n".join(bad), f))
        rows.append((name, designed, applied, caught, caught / applied if applied else None))
    return rows


# ---------------------------------------------------------------------------------------------------------------


def main() -> None:
    cfg = load_yaml("case_summaries.yaml")
    write = WRITERS[cfg["writer"]]
    con = connect(read_only=False)
    cur = con.execute("select * from cases.case_records order by review_date, business_id")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    out, checked = [], []
    for row in rows:
        f = case_fields(row)
        summary = write(f)
        problems = check(summary, f)
        out.append((row["case_id"], row["business_id"], row["review_date"], cfg["writer"], summary, len(problems)))
        checked.append((row["case_id"], f, summary))

    rng = np.random.default_rng(cfg["seed"])
    sample = [checked[i] for i in sorted(rng.choice(len(checked), size=min(cfg["sample_size"], len(checked)), replace=False))]
    rows_measured = measure(sample, rng)

    con.execute("create schema if not exists analysis")
    con.execute("create or replace table analysis.case_summaries (case_id varchar, business_id integer, review_date date, "
                "writer varchar, summary varchar, problems integer)")
    con.executemany("insert into analysis.case_summaries values (?, ?, ?, ?, ?, ?)", out)
    con.execute("create or replace table analysis.summary_checks (corruption varchar, designed_to_catch boolean, "
                "summaries integer, caught integer, catch_rate double)")
    con.executemany("insert into analysis.summary_checks values (?, ?, ?, ?, ?)", rows_measured)
    print(f"{len(out)} summaries, {sum(1 for o in out if o[5])} failing the check")
    for r in rows_measured:
        print(r)
    con.close()


if __name__ == "__main__":
    main()
