-- The rule inventory (module F, ADR-024): one row per rule, running or proposed.
--   owner, rationale, status        config/rules.yaml
--   last changed, last decision     the change log (config/rule_changes.yaml)
--   cutoff                          what it runs at in the recommended rule set (tuned for challenger rules)
--   test-month figures              the rule on its own at that cutoff (bt_sweep_metrics); cases only it caught in
--                                   the recommended set (bt_rule_overlap). Launch controls and vendor signals
--                                   are not in that set, so they have no unique catches here.
--   break-even precision and the latest quarterly recommendation, for rules that run
with changes as (
    select
        rule_id,
        max(change_date)                                                as last_changed,
        count(*)                                                        as changes,
        arg_max(decision, change_no)                                    as last_decision
    from {{ ref('cfg_rule_changes') }}
    group by rule_id
),

running as (
    select distinct rule_id, cutoff from {{ ref('bt_strategy_hits') }} where strategy_id = 'challenger'
),

latest_review as (
    select rule_id, arg_max(recommendation, quarter) as latest_recommendation, max(quarter) as latest_quarter
    from {{ ref('gov_rule_quarterly') }}
    group by rule_id
)

select
    r.rule_id,
    r.owner,
    r.status,
    r.reason_code,
    r.rationale,
    r.action,
    coalesce(run.cutoff, r.threshold)                                   as cutoff,
    run.rule_id is not null                                             as is_running,
    ch.last_changed,
    ch.changes,
    ch.last_decision,
    m.alerts / m.business_days                                          as test_alerts_per_day,
    m.precision                                                         as test_precision,
    m.cases_detected                                                    as test_cases_detected,
    o.cases_only_this_rule                                              as test_unique_cases,
    be.break_even_precision,
    lr.latest_quarter,
    lr.latest_recommendation
from {{ ref('cfg_rules') }} as r
left join running as run using (rule_id)
left join changes as ch using (rule_id)
left join {{ ref('bt_sweep_metrics') }} as m
    on m.rule_id = r.rule_id and abs(m.cutoff - coalesce(run.cutoff, r.threshold)) < 1e-9 and m.period = 'test'
left join {{ ref('bt_rule_overlap') }} as o
    on o.strategy_id = 'challenger' and o.rule_id = r.rule_id and o.period = 'test'
left join {{ ref('gov_break_even') }} as be using (rule_id)
left join latest_review as lr using (rule_id)
