"""The stakeholder pack (module B): one recommendation, three audiences, all numbers from the warehouse.

  docs/stakeholder/exec-one-pager-DRAFT.md   the decision, fraud dollars, customers affected, reviews per day
  docs/stakeholder/ops-brief-DRAFT.md        what changes in the queue on Monday
  docs/stakeholder/eng-ticket-DRAFT.md       events to log, limits to enforce, rollout and kill switch

The recommendation is the current one: add the proposed (challenger) rules to the running (champion) set (ADR-020).
Prose in those files is a draft for me to write; only the marked blocks are generated.
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml

DIR = ROOT / "docs" / "stakeholder"
CANDIDATES = ROOT / "dbt" / "models" / "rules" / "candidates"


def _proposed() -> list[dict]:
    return [r for r in R.challenger_thresholds() if r["status"] == "challenger" and r["is_kept"]]


def evidence_fields(rule_id: str) -> list[str]:
    """The fields a rule's candidate model puts in its evidence: what Engineering must log for it to work."""
    sql = (CANDIDATES / f"cand_{rule_id}.sql").read_text()
    body = re.search(r"json_object\((.*?)\) as evidence", sql, re.S).group(1)
    return re.findall(r"'([a-z0-9_]+)'", body)


def exec_blocks() -> dict[str, str]:
    m, b = R.strategy_metrics("test"), R.bootstrap()
    ch, cl = m["champion"], m["challenger"]
    decision = R.markdown_table(["Proposed rule", "Action", "Fires when"],
                                [(R.RULE_LABELS[r["rule_id"]], R.action_cell(r), R.challenger_cell(r)) for r in _proposed()])
    months = 6
    numbers = R.markdown_table(["Test months (6, held out)", "Today", "With the change", "Difference"], [
        ("Fraud $ prevented", R.usd(ch["loss_prevented"]), R.usd(cl["loss_prevented"]),
         R.ci(b, "challenger_minus_champion", "loss_prevented", R.usd)),
        ("Good businesses flagged", R.num(ch["good_businesses_flagged"]), R.num(cl["good_businesses_flagged"]),
         R.num(cl["good_businesses_flagged"] - ch["good_businesses_flagged"])),
        ("Good businesses with money held", R.num(ch["good_businesses_held"]), R.num(cl["good_businesses_held"]),
         R.num(cl["good_businesses_held"] - ch["good_businesses_held"])),
        ("Reviews per business day", R.num(ch["reviews_per_day"], 1), R.num(cl["reviews_per_day"], 1),
         R.num(cl["reviews_per_day"] - ch["reviews_per_day"], 1)),
    ])
    bust_ch, bust_cl = R.typology_totals("champion")["credit_bust_out"], R.typology_totals("challenger")["credit_bust_out"]
    missed = bust_ch["loss"] - bust_ch["prevented"]
    risk = R.markdown_table(["Risk of not acting", "Value"], [
        ("Bust-out losses today's rules let through (test months)", f"{R.usd(missed)} of {R.usd(bust_ch['loss'])}"),
        ("Of which the change would have stopped", R.usd(bust_cl["prevented"] - bust_ch["prevented"])),
        ("The same, per month", R.usd((bust_cl["prevented"] - bust_ch["prevented"]) / months)),
    ])
    return {"exec-decision": decision, "exec-numbers": numbers, "exec-risk": risk}


def ops_blocks() -> dict[str, str]:
    vol, rules = R.rule_volumes("challenger"), load_yaml("rules.yaml")["rules"]
    codes = R.markdown_table(["New reason code", "Rule", "Action", "Expected cases per business day", "Playbook"],
                             [(f"`{rules[r['rule_id']]['reason_code']}`",
                               R.RULE_LABELS[r["rule_id"]], R.action_cell(r), R.num(vol.get(r["rule_id"], {}).get("cases_per_day", 0), 1),
                               f"[playbook](../playbooks/{r['rule_id']}.md)") for r in _proposed()])
    q, w = R.queue_summary("test"), R.window()
    days = R.strategy_metrics("test")["champion"]["business_days"]
    rows = []
    for label, key, fmt in (("Cases per business day", "cases", lambda v: R.num(v / days, 1)),
                            ("Cases that lapse unreviewed", "lapsed", R.num),
                            ("Good customers held more than 24 hours", "good_holds_over_24h", R.num),
                            ("Fraud $ prevented", "fraud_prevented", R.usd)):
        a, c = q[("champion", "priority")][key], q[("challenger", "priority")][key]
        rows.append((label, fmt(a), fmt(c)))
    queue = R.markdown_table([f"Prioritized queue at {w['reviews_capacity_per_day']:g} reviews/day (test months)", "Today", "With the change"], rows)
    return {"ops-codes": codes, "ops-queue": queue}


def eng_blocks() -> dict[str, str]:
    rules = load_yaml("rules.yaml")["rules"]
    roll = load_yaml("backtest.yaml")["rollout"]
    vol = R.rule_volumes("challenger")
    events = R.markdown_table(["Rule", "Fields it reads (must be logged and available at decision time)"],
                              [(R.RULE_LABELS[r["rule_id"]], ", ".join(f"`{f}`" for f in evidence_fields(r["rule_id"])))
                               for r in _proposed()])
    limits = R.markdown_table(["Rule", "Score", "Cutoff", "Fixed gates", "Action"],
                              [(R.RULE_LABELS[r["rule_id"]], rules[r["rule_id"]]["score"], R.challenger_cell(r),
                                ", ".join(f"{k} = {v:g}" for k, v in rules[r["rule_id"]]["params"].items()), R.action_cell(r))
                               for r in _proposed()])
    rollout = R.markdown_table(["Rule", "Shadow mode", "Expected cases/day", "Kill switch if cases/day exceed"],
                               [(R.RULE_LABELS[r["rule_id"]], f"{roll['shadow_business_days']} business days",
                                 R.num(vol.get(r["rule_id"], {}).get("cases_per_day", 0), 1),
                                 R.num(roll["kill_switch_multiple"] * vol.get(r["rule_id"], {}).get("cases_per_day", 0), 1))
                                for r in _proposed()])
    return {"eng-events": events, "eng-limits": limits, "eng-rollout": rollout}


def documents() -> dict[Path, dict[str, str]]:
    return {DIR / "exec-one-pager-DRAFT.md": exec_blocks(), DIR / "ops-brief-DRAFT.md": ops_blocks(),
            DIR / "eng-ticket-DRAFT.md": eng_blocks()}
