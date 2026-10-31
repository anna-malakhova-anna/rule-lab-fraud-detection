{#
  Backtest building blocks. Only models under models/backtest/ call these: they read the answer key.

  grade_hits(hits)  one row per (strategy, transaction): when several rules in a strategy hit the same
                    transaction, the strongest action wins. Each hit is labelled
                      fraud_txn     the transaction is part of a planted case (a bad check, a stolen payment)
                      fraud_account the account itself is the fraudster's (opened for the scheme, a shell, or a
                                    first-party fraudster after the scheme began): flagging it hurts no good customer
                      good          everything else, including a fraud VICTIM's normal payments
  hits must have: strategy_id, strategy_kind, rule_id, cutoff, txn_id, business_id, event_time, txn_type, amount, action
#}
{% macro grade_hits(hits) -%}
with deduped as (
    select
        h.strategy_id,
        any_value(h.strategy_kind)                      as strategy_kind,
        h.txn_id,
        any_value(h.business_id)                        as business_id,
        any_value(h.event_time)                         as event_time,
        any_value(h.txn_type)                           as txn_type,
        any_value(h.amount)                             as amount,
        arg_max(h.action, a.severity)                   as action,
        string_agg(h.rule_id, ',' order by h.rule_id)   as rules
    from {{ hits }} as h
    join {{ ref('cfg_actions') }} as a using (action)
    group by h.strategy_id, h.txn_id
)

select
    d.*,
    a.prevents,
    a.hold_days,
    a.is_review,
    case
        when ft.txn_id is not null                                                   then 'fraud_txn'
        when c.account_is_fraudulent                                                 then 'fraud_account'
        when c.is_first_party and d.event_time >= c.case_start                      then 'fraud_account'
        else 'good'
    end                                                                              as label,
    case when ft.txn_id is not null or c.account_is_fraudulent
              or (c.is_first_party and d.event_time >= c.case_start)
         then c.case_id end                                                          as case_id,
    case
        when cast(d.event_time as date) <  {{ window_value('window_start') }} then 'warmup'
        when cast(d.event_time as date) <  {{ window_value('train_end') }}    then 'train'
        else 'test'
    end                                                                              as period,
    -- Alerts are worked on business days: a Saturday or Sunday alert lands in Monday's queue.
    cast(d.event_time as date) + case dayofweek(d.event_time) when 6 then 2 when 0 then 1 else 0 end as review_date
from deduped as d
join {{ ref('cfg_actions') }} as a using (action)
left join {{ source('answer_key', 'fraud_txns') }} as ft using (txn_id)
left join {{ ref('bt_cases') }} as c using (business_id)
{%- endmacro %}


{#
  case_outcomes(graded, strategies): per strategy and case, how much of the loss the strategy prevented.
  A loss transaction is prevented (in proportion to the action's `prevents`) by the strongest action that
  landed on the same case at or before it. ADR-003.
#}
{% macro case_outcomes(graded, strategies, label_as_of=none) -%}
with loss_txns as (
    -- With label_as_of, only the cases the bank had confirmed by then exist (ADR-013).
    select l.*
    from {{ ref('bt_loss_txns') }} as l
    join {{ ref('bt_cases') }} as c using (case_id)
    {% if label_as_of %}where c.label_known_at <= {{ label_as_of }}{% endif %}
),

credit as (
    select
        s.strategy_id,
        l.case_id,
        l.txn_id,
        l.loss_amount,
        coalesce(max(g.prevents), 0)    as prevents
    from {{ strategies }} as s
    cross join loss_txns as l
    left join {{ graded }} as g
        on  g.strategy_id = s.strategy_id
        and g.case_id     = l.case_id
        and g.event_time <= l.txn_time
    group by s.strategy_id, l.case_id, l.txn_id, l.loss_amount
),

first_hit as (
    select strategy_id, case_id, min(event_time) as first_hit_time
    from {{ graded }}
    where case_id is not null
    group by strategy_id, case_id
)

select
    cr.strategy_id,
    c.case_id,
    c.typology,
    c.variant,
    c.period,
    c.case_start,
    sum(cr.loss_amount)                                     as loss_if_uncaught,
    sum(cr.loss_amount * cr.prevents)                       as loss_prevented,
    sum(cr.loss_amount * (1 - cr.prevents))                 as loss_missed,
    fh.first_hit_time is not null                           as detected,
    date_diff('minute', c.case_start, fh.first_hit_time) / 60.0 as hours_to_first_hit
from credit as cr
join {{ ref('bt_cases') }} as c using (case_id)
left join first_hit as fh on fh.strategy_id = cr.strategy_id and fh.case_id = cr.case_id
group by all
{%- endmacro %}


{#
  strategy_metrics(graded, cases, strategies, label_as_of): the three trade-offs per strategy and period.
  With label_as_of, a hit on a case not yet confirmed by then counts as a hit on a good customer, as it would
  have looked at the time (ADR-013).
#}
{% macro strategy_metrics(graded, cases, strategies, label_as_of=none) -%}
with graded as (
    select
        g.*,
        {% if label_as_of %}
        case when g.label <> 'good' and (c.label_known_at is null or c.label_known_at > {{ label_as_of }})
             then 'good' else g.label end as eff_label
        {% else %}
        g.label as eff_label
        {% endif %}
    from {{ graded }} as g
    left join {{ ref('bt_cases') }} as c using (case_id)
),

periods as (
    select period, count(*) as business_days
    from {{ ref('bt_business_days') }}
    group by period
),

case_side as (
    select
        strategy_id,
        period,
        count(*)                                    as cases,
        count(*) filter (where detected)            as cases_detected,
        sum(loss_if_uncaught)                       as loss_if_uncaught,
        sum(loss_prevented)                         as loss_prevented,
        sum(loss_missed)                            as loss_missed
    from {{ cases }}
    group by strategy_id, period
),

alert_side as (
    select
        strategy_id,
        period,
        count(*)                                                            as alerts,
        count(*) filter (where eff_label <> 'good')                         as alerts_on_fraud,
        count(distinct business_id) filter (where eff_label = 'good')       as good_businesses_flagged,
        count(distinct business_id) filter (where eff_label = 'good' and hold_days > 0) as good_businesses_held,
        count(*) filter (where eff_label = 'good' and hold_days > 0 and txn_type = 'payroll') as payrolls_delayed,
        count(distinct business_id) filter (where eff_label = 'good' and txn_type = 'application' and action = 'block') as good_applicants_declined,
        coalesce(sum(amount * hold_days) filter (where eff_label = 'good'), 0) as good_dollar_days_held
    from graded
    where period in ('train', 'test')
    group by strategy_id, period
),

-- Reviews: one per business per review day, however many alerts it raised that day.
daily as (
    select g.strategy_id, bd.period, bd.business_date, count(distinct g.business_id) as reviews
    from graded as g
    join {{ ref('bt_business_days') }} as bd on bd.business_date = g.review_date
    where g.is_review
    group by g.strategy_id, bd.period, bd.business_date
),

review_side as (
    select
        d.strategy_id,
        d.period,
        sum(d.reviews)                                                       as reviews,
        sum(d.reviews) / any_value(p.business_days)                          as reviews_per_day,
        quantile_cont(d.reviews, 0.95)                                       as reviews_p95_day,
        max(d.reviews)                                                       as reviews_max_day,
        count(*) filter (where d.reviews > {{ window_value('reviews_capacity_per_day') }}) as days_over_capacity
    from daily as d
    join periods as p using (period)
    group by d.strategy_id, d.period
)

select
    s.strategy_id,
    s.strategy_kind,
    s.rule_id,
    s.cutoff,
    p.period,
    p.business_days,
    coalesce(cs.cases, 0)                                           as cases,
    coalesce(cs.cases_detected, 0)                                  as cases_detected,
    coalesce(cs.cases_detected, 0) / nullif(cs.cases, 0)            as case_recall,
    coalesce(cs.loss_if_uncaught, 0)                                as loss_if_uncaught,
    coalesce(cs.loss_prevented, 0)                                  as loss_prevented,
    coalesce(cs.loss_missed, 0)                                     as loss_missed,
    coalesce(cs.loss_prevented, 0) / nullif(cs.loss_if_uncaught, 0) as dollar_recall,
    coalesce(a.alerts, 0)                                           as alerts,
    coalesce(a.alerts_on_fraud, 0)                                  as alerts_on_fraud,
    a.alerts_on_fraud / nullif(a.alerts, 0)                         as precision,
    coalesce(a.good_businesses_flagged, 0)                          as good_businesses_flagged,
    coalesce(a.good_businesses_held, 0)                             as good_businesses_held,
    coalesce(a.payrolls_delayed, 0)                                 as payrolls_delayed,
    coalesce(a.good_applicants_declined, 0)                         as good_applicants_declined,
    coalesce(a.good_dollar_days_held, 0)                            as good_dollar_days_held,
    coalesce(r.reviews, 0)                                          as reviews,
    coalesce(r.reviews_per_day, 0)                                  as reviews_per_day,
    coalesce(r.reviews_p95_day, 0)                                  as reviews_p95_day,
    coalesce(r.reviews_max_day, 0)                                  as reviews_max_day,
    coalesce(r.days_over_capacity, 0)                               as days_over_capacity,
    -- Net value in dollars, using the stated costs in config/backtest.yaml (ADR-008).
    coalesce(cs.loss_prevented, 0)
      - {{ cost('review_cost') }}               * coalesce(r.reviews, 0)
      - {{ cost('good_customer_touch_cost') }}  * coalesce(a.good_businesses_flagged, 0)
      - {{ cost('hold_cost_per_dollar_day') }}  * coalesce(a.good_dollar_days_held, 0)
      - {{ cost('payroll_delay_cost') }}        * coalesce(a.payrolls_delayed, 0)
      - {{ cost('good_applicant_decline_cost') }} * coalesce(a.good_applicants_declined, 0) as net_value
from {{ strategies }} as s
cross join periods as p
left join case_side   as cs on cs.strategy_id = s.strategy_id and cs.period = p.period
left join alert_side  as a  on a.strategy_id  = s.strategy_id and a.period  = p.period
left join review_side as r  on r.strategy_id  = s.strategy_id and r.period  = p.period
{%- endmacro %}
