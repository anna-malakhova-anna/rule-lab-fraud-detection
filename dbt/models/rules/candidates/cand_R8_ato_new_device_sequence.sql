-- The account-takeover sequence: a login from a never-seen device, then a change to the email or phone on
-- file, then the FIRST payment to a payee that was added after that login. Score: hours since the new device.
select
    'R8_ato_new_device_sequence'              as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    hours_since_new_device                    as score,
    true                                      as escalation_eligible,
    json_object('hours_since_new_device', hours_since_new_device, 'contact_changes_since_new_device', contact_changes_since_new_device, 'payee_added_after_new_device', payee_added_after_new_device) as evidence,
    printf('new device %.1f hours before; %d contact change(s) since; first payment to a payee added after that login',
           hours_since_new_device, contact_changes_since_new_device) as detail
from {{ ref('feat_payment_signals') }}
where is_first_payment_to_payee
  and payee_added_after_new_device
  and contact_changes_since_new_device > 0
  and hours_since_new_device <= {{ rule_param('R8_ato_new_device_sequence', 'lookback_hours') }}
