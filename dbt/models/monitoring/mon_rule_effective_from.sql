-- A rule written in response to a monitoring alarm (config: effective_from_alarm) starts running when the
-- first alarm on that series inside the window has closed, plus the investigation time in business days
-- (converted to calendar days, 5 business days to 7). Rules without an alarm run from the start.
with first_alarm as (
    select series, min(week_closes_at) as detected_at
    from {{ ref('mon_return_alarms') }}
    where is_alarm and week >= {{ window_value('window_start') }}
    group by series
)

select
    r.rule_id,
    r.effective_from_alarm                                                    as alarm_series,
    f.detected_at,
    f.detected_at + to_days(cast(ceil(m.investigation_business_days * 7 / 5.0) as integer)) as effective_from
from {{ ref('cfg_rules') }} as r
cross join {{ ref('cfg_monitoring') }} as m
left join first_alarm as f on f.series = r.effective_from_alarm
where coalesce(r.effective_from_alarm, '') <> ''
