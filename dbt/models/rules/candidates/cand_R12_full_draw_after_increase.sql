-- Draws that take the line close to its limit soon after the limit was raised. Score: days since the increase.
select
    'R12_full_draw_after_increase'            as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    'loc_draw'                                as txn_type,
    amount,
    days_since_limit_increase                 as score,
    true                                      as escalation_eligible,
    json_object('amount', amount, 'utilisation_after', utilisation_after, 'current_limit', current_limit, 'days_since_limit_increase', days_since_limit_increase) as evidence,
    printf('draw of $%,.0f takes the line to %.0f%% of a $%,.0f limit raised %.1f days ago', amount,
           100 * utilisation_after, current_limit, days_since_limit_increase) as detail
from {{ ref('feat_credit_draws') }}
where days_since_limit_increase is not null
  and utilisation_after >= {{ rule_param('R12_full_draw_after_increase', 'min_utilisation') }}
