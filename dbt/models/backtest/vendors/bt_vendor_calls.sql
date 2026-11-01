-- How many calls each vendor and call strategy would have paid for, per period (ADR-022).
select
    s.strategy_id,
    s.vendor,
    s.call_strategy,
    case when cast(c.called_at as date) < {{ window_value('train_end') }} then 'train' else 'test' end as period,
    count(*)                                                           as calls,
    count(*) filter (where c.covered)                                  as answered,
    median(c.latency_ms)                                               as median_latency_ms
from {{ ref('bt_vendor_strategies') }} as s
join {{ ref('vnd_call_points') }} as c on c.vendor = s.vendor
where s.strategy_kind = 'vendor'
  and cast(c.called_at as date) >= {{ window_value('window_start') }}
  and (s.call_strategy = 'always'
       or (s.call_strategy = 'onboarding_only' and c.call_point = 'application')
       or (s.call_strategy = 'risk_gated' and c.risk_gated_call))
group by all
