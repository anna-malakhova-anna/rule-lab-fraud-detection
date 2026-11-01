-- What an analyst sees when a case opens (module G, ADR-025): one record per business per review day, built only
-- from bank data and the rules' own output. The case summaries (scripts/case_summaries.py) may cite these fields
-- and nothing else. No answer key: an analyst does not know the truth either.
-- The rules are today's rules plus the proposed ones, at their configured cutoffs; only actions an analyst reviews.
with alerts as (
    select
        h.business_id,
        cast(h.event_time as date) + case dayofweek(h.event_time) when 6 then 2 when 0 then 1 else 0 end as review_date,
        h.rule_id, h.reason_code, h.action, a.severity, h.event_time, h.txn_type, h.amount, h.score, h.evidence
    from {{ ref('rule_hits') }} as h
    join {{ ref('cfg_actions') }} as a using (action)
    where h.status in ('champion', 'challenger') and a.is_review
      and cast(h.event_time as date) >= {{ window_value('window_start') }}
      and cast(h.event_time as date) <  {{ window_value('window_end') }}
)

select
    a.business_id || '-' || strftime(a.review_date, '%Y%m%d')                     as case_id,
    a.business_id,
    a.review_date,
    arg_max(a.action, a.severity)                                                 as action,
    any_value(b.legal_name)                                                       as legal_name,
    any_value(b.industry)                                                         as industry,
    any_value(b.open_date)                                                        as open_date,
    any_value(date_diff('day', b.open_date, a.review_date))                       as tenure_days,
    any_value(b.stated_monthly_revenue)                                           as stated_monthly_revenue,
    list({'rule_id': a.rule_id, 'reason_code': a.reason_code, 'action': a.action, 'event_time': a.event_time,
          'txn_type': a.txn_type, 'amount': a.amount, 'score': a.score, 'evidence': a.evidence}
         order by a.severity desc, a.amount desc, a.event_time, a.rule_id)        as alerts
from alerts as a
join {{ ref('stg_businesses') }} as b using (business_id)
group by a.business_id, a.review_date
