-- Check deposits measured against the account's own normal monthly inflow. Young accounts have no
-- baseline yet, so they are measured against the revenue they stated at onboarding.
with scored as (
    select
        *,
        case
            when history_days >= {{ rule_param('R2_check_vs_own_baseline', 'min_history_days') }}
                 and baseline_monthly_inflow > 0
            then baseline_monthly_inflow
            else stated_monthly_revenue
        end as reference_monthly_inflow,
        history_days < {{ rule_param('R2_check_vs_own_baseline', 'min_history_days') }} as uses_stated_revenue
    from {{ ref('feat_check_deposits') }}
    where amount >= {{ rule_param('R2_check_vs_own_baseline', 'min_amount') }}
)

select
    'R2_check_vs_own_baseline'                as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    'mobile_check_deposit'                    as txn_type,
    amount,
    amount / nullif(reference_monthly_inflow, 0) as score,
    true                                      as escalation_eligible,
    printf('$%,.0f check vs $%,.0f/month %s', amount, reference_monthly_inflow,
           case when uses_stated_revenue then 'stated revenue' else 'trailing inflow' end) as detail
from scored
