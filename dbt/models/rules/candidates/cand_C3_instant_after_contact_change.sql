-- Launch control: a cooling-off period after a change of email or phone on file, or a login from a new device.
-- Score: hours since the most recent of those.
select
    'C3_instant_after_contact_change'         as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    least(coalesce(hours_since_contact_change, 1e9), coalesce(hours_since_new_device, 1e9)) as score,
    true                                      as escalation_eligible,
    json_object('hours_since_contact_change', hours_since_contact_change,
                'hours_since_new_device', hours_since_new_device, 'amount', amount) as evidence,
    printf('instant payout of $%,.0f %.1f hours after a contact change or new device', amount,
           least(coalesce(hours_since_contact_change, 1e9), coalesce(hours_since_new_device, 1e9))) as detail
from {{ ref('feat_payment_signals') }}
where is_instant and (hours_since_contact_change is not null or hours_since_new_device is not null)
