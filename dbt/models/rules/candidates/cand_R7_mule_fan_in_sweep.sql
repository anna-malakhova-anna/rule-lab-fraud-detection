-- Outbound payments from an account that has been paid by many first-time senders in the last 14 days and has
-- already sent most of that money back out. Score: how many first-time senders.
select
    'R7_mule_fan_in_sweep'                    as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    cast(new_senders_14d as double)           as score,
    true                                      as escalation_eligible,
    json_object('new_senders_14d', new_senders_14d, 'new_sender_inbound_14d', new_sender_inbound_14d, 'out_14d_incl_this', out_14d_incl_this) as evidence,
    printf('%d first-time senders paid $%,.0f in 14 days; $%,.0f went out', new_senders_14d,
           new_sender_inbound_14d, out_14d_incl_this) as detail
from {{ ref('feat_payment_signals') }}
where txn_type <> 'payroll'
  and new_sender_inbound_14d >= {{ rule_param('R7_mule_fan_in_sweep', 'min_new_sender_inbound') }}
  and out_14d_incl_this >= {{ rule_param('R7_mule_fan_in_sweep', 'min_swept_share') }} * new_sender_inbound_14d
