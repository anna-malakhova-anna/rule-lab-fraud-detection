-- R1's logic on credit draws: outbound payments made while money drawn on the line in the last 72 hours is in
-- the account, scored by the share of it that already left on top of a normal week of spending. A failing
-- business draws to pay staff and suppliers over weeks; a bust-out sends the draw out within hours.
select
    'R11_draw_then_fast_out'                  as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    excess_out_48h_vs_line_draws              as score,
    true                                      as escalation_eligible,
    printf('$%,.0f out in 48h (normal week $%,.0f) vs $%,.0f drawn on the line in 72h',
           out_48h_incl_this, normal_week_outflow, line_draws_prior_72h) as detail
from {{ ref('feat_payment_signals') }}
where txn_type <> 'payroll'
  and line_draws_prior_72h >= {{ rule_param('R11_draw_then_fast_out', 'min_recent_draws') }}
