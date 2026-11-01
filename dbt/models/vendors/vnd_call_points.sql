-- Every point at which a vendor could be called, with its answer, and whether the risk-gated call strategy would
-- call it (ADR-022). Gates use in-house signals only:
--   application       it shares an identity attribute with an earlier application (feat_applications)
--   new_device_login  a contact change in the 72 hours before
--   contact_change    a new-device login in the 72 hours before
with answers as (
    select 'tallowmere' as vendor, * from {{ source('raw', 'vendor_tallowmere') }}
    union all
    select 'quenchwire', * from {{ source('raw', 'vendor_quenchwire') }}
    union all
    select 'larchstone', * from {{ source('raw', 'vendor_larchstone') }}
),

new_device_logins as (
    select event_id, business_id, event_time
    from {{ ref('stg_events') }}
    where event_type = 'login'
    qualify row_number() over (partition by business_id, device_id order by event_time, event_id) = 1
),

contact_changes as (
    select event_id, business_id, event_time
    from {{ ref('stg_events') }}
    where event_type in ('email_changed', 'phone_changed')
)

select
    a.vendor,
    a.call_point,
    a.call_point_id,
    a.business_id,
    a.called_at,
    a.covered,
    a.score,
    a.result,
    a.latency_ms,
    case a.call_point
        when 'application' then (select f.max_shared_with_one >= 1 from {{ ref('feat_applications') }} as f
                                 where f.application_id = a.call_point_id)
        when 'new_device_login' then exists (
            select 1 from contact_changes as c
            where c.business_id = a.business_id and c.event_time between a.called_at - interval 72 hour and a.called_at)
        when 'contact_change' then exists (
            select 1 from new_device_logins as d
            where d.business_id = a.business_id and d.event_time between a.called_at - interval 72 hour and a.called_at)
    end                                                             as risk_gated_call
from answers as a
