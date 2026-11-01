-- The quarterly rule review (module F, ADR-024), run after every quarter of the window on the recommended rule set
-- (the challenger). Each review uses only what the bank knew on its review day (reviewed_on): the quarter's end
-- plus label_maturity_days (config/governance.yaml). A rule whose fraud is confirmed late is judged on an older
-- quarter of its alerts (lag_quarters), so a missing label is not mistaken for a false alarm.
--   low precision     precision below the rule's break-even (gov_break_even), on at least min_alerts alerts
--   added value       fraud dollars the challenger prevents that it would not without this rule (leave one out),
--                     on losses confirmed by the review day. Catching a case earlier counts, not only catching it
--                     alone, so this is fairer than "cases only this rule caught" (shown alongside).
--   drift             alerts per business day moved by drift_ratio or more against the previous judged quarter
-- Recommendation, strongest first: retire candidate (no added value for reviews_without_added_value reviews in a
-- row), retune (low precision), investigate drift, keep. A rule with no judged quarter yet is "too early".
{% set gov = "(select value from " ~ ref('cfg_governance') ~ " where param = '%s')" %}
with quarters as (
    select
        row_number() over (order by q)                                  as q_no,
        q                                                               as quarter_start,
        q + interval 3 month                                            as quarter_end,
        year(q) || '-Q' || quarter(q)                                   as quarter_name
    from (select unnest(generate_series(cast({{ window_value('window_start') }} as timestamp),
                                        cast({{ window_value('window_end') }} as timestamp) - interval 1 day,
                                        interval 3 month)) as q)
),

-- One review per quarter end and running rule, with the quarter of alerts it judges.
reviews as (
    select
        q.quarter_name                                                  as quarter,
        cast(q.quarter_end as date) + cast({{ gov % 'label_maturity_days' }} as integer) as reviewed_on,
        b.rule_id,
        b.break_even_precision,
        lag.lag_quarters,
        j.quarter_name                                                  as judged_quarter,
        j.quarter_start                                                 as judged_start,
        j.quarter_end                                                   as judged_end
    from quarters as q
    cross join {{ ref('gov_break_even') }} as b
    join {{ ref('cfg_review_lag') }} as lag using (rule_id)
    left join quarters as j on j.q_no = q.q_no - lag.lag_quarters
),

days as (
    select q.quarter_name as judged_quarter, count(*) as business_days
    from quarters as q
    join {{ ref('bt_business_days') }} as d on d.business_date >= q.quarter_start and d.business_date < q.quarter_end
    group by q.quarter_name
),

challenger_hits as (
    select g.txn_id, g.event_time, g.label, g.case_id, unnest(string_split(g.rules, ',')) as rule_id
    from {{ ref('bt_strategy_graded') }} as g
    where g.strategy_id = 'challenger'
),

-- The judged quarter's alerts; one counts as fraud only if its case was confirmed by the review day.
judged as (
    select
        r.quarter, r.rule_id, h.txn_id, h.case_id,
        h.label <> 'good' and c.label_known_at <= r.reviewed_on        as known_fraud,
        r.reviewed_on
    from reviews as r
    join challenger_hits as h
        on h.rule_id = r.rule_id and h.event_time >= r.judged_start and h.event_time < r.judged_end
    left join {{ ref('bt_cases') }} as c on c.case_id = h.case_id
),

-- How many rules in the set touched each case (any time before the review day): 1 means this rule alone.
case_rule_counts as (
    select j.quarter, j.case_id, count(distinct h.rule_id) as n_rules
    from (select distinct quarter, case_id, reviewed_on from judged where known_fraud) as j
    join challenger_hits as h on h.case_id = j.case_id and h.event_time < j.reviewed_on
    group by j.quarter, j.case_id
),

alert_side as (
    select
        j.quarter, j.rule_id,
        count(distinct j.txn_id)                                        as alerts,
        count(distinct j.txn_id) filter (where j.known_fraud)           as alerts_on_known_fraud,
        count(distinct j.case_id) filter (where j.known_fraud)          as cases_caught,
        count(distinct j.case_id) filter (where j.known_fraud and crc.n_rules = 1) as unique_cases
    from judged as j
    left join case_rule_counts as crc on crc.quarter = j.quarter and crc.case_id = j.case_id
    group by j.quarter, j.rule_id
),

-- Leave one out: confirmed losses in the judged quarter the challenger prevents and challenger-minus-this-rule does not.
added_value as (
    select
        r.quarter, r.rule_id,
        sum(full_set.loss_amount * (full_set.prevents - without.prevents)) as added_value
    from reviews as r
    join {{ ref('bt_loss_credit') }} as full_set
        on full_set.strategy_id = 'challenger'
       and full_set.txn_time >= r.judged_start and full_set.txn_time < r.judged_end
    join {{ ref('bt_loss_credit') }} as without
        on without.strategy_id = 'without:' || r.rule_id and without.txn_id = full_set.txn_id
    join {{ ref('bt_cases') }} as c on c.case_id = full_set.case_id and c.label_known_at <= r.reviewed_on
    group by r.quarter, r.rule_id
),

per_review as (
    select
        r.quarter, r.reviewed_on, r.rule_id, r.lag_quarters, r.judged_quarter, r.break_even_precision,
        d.business_days,
        coalesce(a.alerts, 0)                                           as alerts,
        coalesce(a.alerts, 0) / d.business_days                         as alerts_per_day,
        coalesce(a.alerts_on_known_fraud, 0)                            as alerts_on_known_fraud,
        a.alerts_on_known_fraud / nullif(a.alerts, 0)                   as precision_known,
        coalesce(a.cases_caught, 0)                                     as cases_caught,
        coalesce(a.unique_cases, 0)                                     as unique_cases,
        coalesce(v.added_value, 0)                                      as added_value
    from reviews as r
    left join days as d using (judged_quarter)
    left join alert_side as a using (quarter, rule_id)
    left join added_value as v using (quarter, rule_id)
),

flagged as (
    select
        *,
        alerts_per_day / nullif(lag(alerts_per_day) over w, 0)          as volume_vs_previous_quarter,
        coalesce(lag(alerts) over w >= {{ gov % 'min_alerts' }}
                 and (alerts_per_day / nullif(lag(alerts_per_day) over w, 0) >= {{ gov % 'drift_ratio' }}
                      or alerts_per_day / nullif(lag(alerts_per_day) over w, 0) <= 1 / {{ gov % 'drift_ratio' }}),
                 false)                                                 as drift,
        alerts >= {{ gov % 'min_alerts' }}
            and coalesce(precision_known, 0) < coalesce(break_even_precision, 0) as low_precision,
        added_value <= 0                                                as no_added_value
    from per_review
    where judged_quarter is not null
    window w as (partition by rule_id order by quarter)
)

select
    r.quarter,
    r.reviewed_on,
    r.rule_id,
    r.lag_quarters,
    r.judged_quarter,
    f.alerts,
    f.alerts_per_day,
    f.alerts_on_known_fraud,
    f.precision_known,
    r.break_even_precision,
    f.cases_caught,
    f.unique_cases,
    f.added_value,
    f.volume_vs_previous_quarter,
    coalesce(f.low_precision, false)                                    as low_precision,
    coalesce(f.no_added_value, false)                                   as no_added_value,
    coalesce(f.drift, false)                                            as drift,
    case
        when f.rule_id is null then 'too early'
        when sum(case when f.no_added_value then 1 else 0 end) over (
                 partition by r.rule_id order by r.quarter
                 rows between cast({{ gov % 'reviews_without_added_value' }} as integer) - 1 preceding and current row
             ) = {{ gov % 'reviews_without_added_value' }}             then 'retire candidate'
        when f.low_precision                                            then 'retune'
        when f.drift                                                    then 'investigate drift'
        else 'keep'
    end                                                                 as recommendation
from reviews as r
left join flagged as f using (quarter, rule_id)
