-- V2_contact_vendor: the vendor's score as a rule, as if every call point were called (the "always" call strategy).
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
    where c.vendor = 'quenchwire' and c.call_point = 'application' and c.covered
),

payments as (
    -- The highest score among this vendor's call points in the 7 days before the payment.
    select
        txn_id,
        any_value(business_id)                as business_id,
        any_value(txn_time)                   as event_time,
        any_value(txn_type)                   as txn_type,
        any_value(amount)                     as amount,
        max(score)                            as score,
        true                                  as escalation_eligible,
        json_object('vendor', 'quenchwire', 'call_point', 'contact_change', 'score', max(score)) as evidence,
        printf('quenchwire scored a contact change in the 7 days before this payment %.0f', max(score)) as detail
    from {{ ref('vnd_payment_links') }}
    where vendor = 'quenchwire'
    group by txn_id
)

select 'V2_contact_vendor' as rule_id, * from applications
union all
select 'V2_contact_vendor', * from payments
