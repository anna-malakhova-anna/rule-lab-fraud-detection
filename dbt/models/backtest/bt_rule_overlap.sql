-- Which rule catches what, inside each rule set. A rule whose catches are all caught by another rule as well
-- adds alerts without adding protection: a candidate to retire.
with rule_list as (
    select distinct strategy_id, rule_id from {{ ref('bt_strategy_hits') }}
),

case_rules as (
    -- Which rules touched each case before or at its last loss, per strategy.
    select distinct g.strategy_id, g.case_id, unnest(string_split(g.rules, ',')) as rule_id
    from {{ ref('bt_strategy_graded') }} as g
    where g.case_id is not null
),

case_rule_counts as (
    select strategy_id, case_id, count(*) as n_rules
    from case_rules
    group by strategy_id, case_id
)

select
    rl.strategy_id,
    rl.rule_id,
    c.period,
    count(distinct cr.case_id)                                      as cases_detected,
    count(distinct cr.case_id) filter (where crc.n_rules = 1)       as cases_only_this_rule,
    coalesce(sum(c.loss_if_uncaught) filter (where crc.n_rules = 1), 0) as loss_in_cases_only_this_rule
from rule_list as rl
left join case_rules as cr on cr.strategy_id = rl.strategy_id and cr.rule_id = rl.rule_id
left join case_rule_counts as crc on crc.strategy_id = cr.strategy_id and crc.case_id = cr.case_id
left join {{ ref('bt_cases') }} as c on c.case_id = cr.case_id
group by rl.strategy_id, rl.rule_id, c.period
