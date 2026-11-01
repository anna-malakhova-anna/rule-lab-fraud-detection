-- Credit decisions (a line opening or a limit-increase request) made right after the account's inflows jumped
-- above its own longer history. Score: last 30 days of inflow / average month of the 90 days before that.
-- Seasonal businesses ramping into their peak look like this too.
select
    'R10_credit_inflow_ramp'                  as rule_id,
    credit_event_id                           as txn_id,
    business_id,
    event_time,
    event_type                                as txn_type,
    0.0                                       as amount,
    inflow_ramp_ratio                         as score,
    true                                      as escalation_eligible,
    json_object('event_type', event_type, 'inflow_last_30d', inflow_last_30d, 'baseline_monthly_inflow_31_120d', baseline_monthly_inflow_31_120d, 'share_last_30d_from_new_payers', share_last_30d_from_new_payers) as evidence,
    printf('%s: $%,.0f in last 30 days vs $%,.0f/month before; %.0f%% of it from payers new in 60 days', event_type,
           inflow_last_30d, baseline_monthly_inflow_31_120d, 100 * coalesce(share_last_30d_from_new_payers, 0)) as detail
from {{ ref('feat_credit_events') }}
where inflow_last_30d >= {{ rule_param('R10_credit_inflow_ramp', 'min_recent_inflow') }}
  and inflow_ramp_ratio is not null
