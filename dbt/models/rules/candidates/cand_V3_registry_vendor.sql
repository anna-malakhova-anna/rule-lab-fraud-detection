-- V3_registry_vendor: the vendor's score as a rule, as if every call point were called (the "always" call strategy).
-- Applications get the rule's own action (an RFI); payments are eligible for its escalation (a hold). The vendor
-- bake-off (models/backtest/vendors/) grades the cheaper call strategies from the same call points.
with applications as (
    select
        c.call_point_id                       as txn_id,
        c.business_id,
        a.applied_at                          as event_time,
        'application'                         as txn_type,
        0.0                                   as amount,
        c.score,
        false                                 as escalation_eligible,
        json_object('vendor', c.vendor, 'call_point', c.call_point, 'score', c.score, 'result', c.result) as evidence,
        printf('%s scored the application %.0f%s', c.vendor, c.score,
               case when c.result <> '' then ' (' || c.result || ')' else '' end) as detail
    from {{ ref('vnd_call_points') }} as c
    join {{ ref('stg_applications') }} as a on a.application_id = c.call_point_id and a.decision = 'approved'
    where c.vendor = 'larchstone' and c.call_point = 'application' and c.covered
)

select 'V3_registry_vendor' as rule_id, * from applications
