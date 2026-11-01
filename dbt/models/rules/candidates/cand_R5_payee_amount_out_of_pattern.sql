-- Payments to an established payee, scored by how far the amount sits above the usual amount for that payee.
select
    'R5_payee_amount_out_of_pattern'          as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    amount_vs_payee_median                    as score,
    true                                      as escalation_eligible,
    json_object('amount', amount, 'payee_median_last6', payee_median_last6, 'prior_payments_to_payee', prior_payments_to_payee) as evidence,
    printf('$%,.0f vs usual $%,.0f to this payee', amount, payee_median_last6) as detail
from {{ ref('feat_outbound_payments') }}
where prior_payments_to_payee >= {{ rule_param('R5_payee_amount_out_of_pattern', 'min_prior_payments') }}
  and amount >= {{ rule_param('R5_payee_amount_out_of_pattern', 'min_amount') }}
