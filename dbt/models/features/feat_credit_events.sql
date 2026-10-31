-- One row per credit decision point (a line opening or a limit-increase request), with the account's inflows
-- just before it against its own longer history. A bust-out pumps inflows up right before asking for more.
with decisions as (
    select credit_event_id, business_id, event_time, event_type, limit_after as current_limit
    from {{ ref('stg_credit_line_events') }}
    where event_type in ('line_opened', 'limit_increase_requested')
),

inflows as (
    -- Money in from outside the business: no internal transfers, no draws on the line itself.
    select business_id, txn_time, amount, counterparty_id
    from {{ ref('stg_transactions') }}
    where direction = 'in' and not is_internal and txn_type <> 'loc_draw'
),

first_paid as (
    select business_id, counterparty_id, min(txn_time) as first_paid_at
    from inflows
    where counterparty_id is not null
    group by business_id, counterparty_id
),

-- Self-join: inflows in the 120 days before each decision, split into the last 30 days and the 90 before that.
windows as (
    select
        d.credit_event_id,
        coalesce(sum(i.amount) filter (where i.txn_time >= d.event_time - interval 30 day), 0)  as inflow_last_30d,
        coalesce(sum(i.amount) filter (where i.txn_time <  d.event_time - interval 30 day), 0)  as inflow_prior_90d,
        coalesce(sum(i.amount) filter (where i.txn_time >= d.event_time - interval 30 day
                                         and f.first_paid_at >= d.event_time - interval 60 day), 0) as inflow_last_30d_new_payers
    from decisions as d
    join inflows as i
        on  i.business_id = d.business_id
        and i.txn_time <  d.event_time
        and i.txn_time >= d.event_time - interval 120 day
    left join first_paid as f
        on f.business_id = i.business_id and f.counterparty_id = i.counterparty_id
    group by d.credit_event_id
)

select
    d.*,
    coalesce(w.inflow_last_30d, 0)                                              as inflow_last_30d,
    coalesce(w.inflow_prior_90d, 0) / 3                                         as baseline_monthly_inflow_31_120d,
    coalesce(w.inflow_last_30d, 0) / nullif(coalesce(w.inflow_prior_90d, 0) / 3, 0) as inflow_ramp_ratio,
    coalesce(w.inflow_last_30d_new_payers, 0) / nullif(w.inflow_last_30d, 0)     as share_last_30d_from_new_payers
from decisions as d
left join windows as w using (credit_event_id)
