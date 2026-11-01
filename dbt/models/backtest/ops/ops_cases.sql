-- Alerts become cases (module A, ADR-019): one case per business per review day, per rule set. A case carries
-- everything an analyst queue needs, and a priority score = expected loss x likelihood:
--   exposure   what is at stake if the case is fraud: the payment or deposit amount; for an application, the
--              stated monthly revenue; for a credit decision, the line's current limit. Raw data only.
--   likelihood the highest known precision among the case's rules (ops_rule_likelihood).
-- The priority uses NO answer-key column. The truth columns at the end (is_fraud, fraud_case_id) are there only
-- to grade the queue simulation afterwards.
with hits as (
    select
        g.*,
        unnest(string_split(g.rules, ','))                         as rule_id
    from {{ ref('bt_strategy_graded') }} as g
    where g.period in ('train', 'test') and g.is_review          -- automatic actions (a launch control's delay) need no analyst
),

-- One row per alerted entity per rule set: its exposure and the best likelihood among the rules that hit it.
per_entity as (
    select
        h.strategy_id, h.txn_id, h.business_id,
        any_value(h.event_time)                                     as event_time,
        any_value(h.review_date)                                    as review_date,
        any_value(h.action)                                         as action,
        any_value(sev.severity)                                     as severity,
        any_value(h.txn_type)                                       as txn_type,
        any_value(h.label)                                          as label,
        any_value(h.case_id)                                        as case_id,
        any_value(h.hold_days)                                      as hold_days,
        any_value(case
            when h.txn_type = 'application'
                then a.stated_monthly_revenue * {{ ops_param('application_exposure_months_of_revenue') }}
            when h.txn_type in ('line_opened', 'limit_increase_requested') then ce.current_limit
            else h.amount
        end)                                                        as exposure,
        string_agg(h.rule_id, ',' order by h.rule_id)               as rules,
        string_agg(r.reason_code, ',' order by r.reason_code)       as reason_codes,
        max(l.likelihood)                                           as likelihood
    from hits as h
    join {{ ref('cfg_rules') }} as r using (rule_id)
    join {{ ref('cfg_actions') }} as sev on sev.action = h.action
    left join {{ ref('ops_rule_likelihood') }} as l using (strategy_id, rule_id)
    left join {{ ref('stg_applications') }} as a on h.txn_type = 'application' and a.application_id = h.txn_id
    left join {{ ref('feat_credit_events') }} as ce on ce.credit_event_id = h.txn_id
    group by h.strategy_id, h.txn_id, h.business_id
)

select
    strategy_id,
    business_id,
    review_date,
    case when review_date < {{ window_value('train_end') }} then 'train' else 'test' end   as period,
    min(event_time)                                                 as opened_at,
    count(*)                                                        as alerts,
    list_sort(list_distinct(flatten(list(string_split(rules, ',')))))           as rule_list,
    list_sort(list_distinct(flatten(list(string_split(reason_codes, ',')))))    as reason_code_list,
    -- The strongest action decides how long the case may wait (cfg ops.review_window_business_days).
    arg_max(action, severity)                                       as action,
    bool_or(txn_type = 'payroll' and hold_days > 0)                 as holds_payroll,
    sum(exposure)                                                   as exposure,
    max(likelihood)                                                 as likelihood,
    sum(exposure) * max(likelihood)                                 as priority,
    -- Truth, for grading only:
    bool_or(label <> 'good')                                        as is_fraud,
    max(case_id)                                                    as fraud_case_id
from per_entity
group by strategy_id, business_id, review_date
