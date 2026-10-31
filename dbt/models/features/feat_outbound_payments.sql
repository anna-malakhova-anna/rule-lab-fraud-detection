-- One row per outbound payment (ACH, wire, payroll), with point-in-time features about the account's recent
-- check deposits and about the payee: history, usual amount, and when its bank details last changed.
with payments as (
    select txn_id, business_id, account_id, txn_time, txn_date, txn_type, amount, payee_id, bank_details_id
    from {{ ref('stg_transactions') }}
    where is_payment_out
),

checks as (
    select business_id, txn_time, amount
    from {{ ref('stg_transactions') }}
    where is_check_deposit
),

-- Self-join to check deposits in the 72 hours up to this payment: money that cannot have cleared yet.
recent_checks as (
    select p.txn_id, sum(c.amount) as checks_prior_72h, count(*) as checks_prior_72h_count
    from payments as p
    join checks as c
        on  c.business_id = p.business_id
        and c.txn_time >= p.txn_time - interval 72 hour
        and c.txn_time <= p.txn_time
    group by p.txn_id
),

-- The payee's most recent master-data event (created or bank details changed) at or before the payment.
last_payee_event as (
    select p.txn_id, e.event_type as last_payee_event_type, e.event_time as last_payee_event_time
    from payments as p
    join {{ ref('stg_payee_events') }} as e
        on e.payee_id = p.payee_id and e.event_time <= p.txn_time
    qualify row_number() over (partition by p.txn_id order by e.event_time desc, e.payee_event_id desc) = 1
),

payment_history as (
    select
        p.*,
        -- Outbound money in the 48 hours up to and including this payment (same business).
        sum(amount) over (partition by business_id order by txn_time
                          range between interval 48 hour preceding and current row)               as out_48h_incl_this,
        row_number() over (partition by payee_id order by txn_time, txn_id) - 1                  as prior_payments_to_payee,
        median(amount) over (partition by payee_id order by txn_time, txn_id
                             rows between 6 preceding and 1 preceding)                           as payee_median_last6,
        row_number() over (partition by payee_id, bank_details_id order by txn_time, txn_id)     as seq_on_bank_details,
        floor(log10(amount))                                                                       as amount_band,
        max(floor(log10(amount))) over (partition by payee_id order by txn_time, txn_id
                                        rows between unbounded preceding and 1 preceding)        as max_prior_amount_band
    from payments as p
)

select
    h.txn_id,
    h.business_id,
    h.account_id,
    h.txn_time,
    h.txn_date,
    h.txn_type,
    h.amount,
    h.payee_id,
    py.payee_type,
    h.bank_details_id,
    h.txn_date - b.open_date                                                     as days_since_open,
    date_diff('second', py.created_at, h.txn_time) / 86400.0                     as days_since_payee_created,
    coalesce(rc.checks_prior_72h, 0)                                             as checks_prior_72h,
    coalesce(rc.checks_prior_72h_count, 0)                                       as checks_prior_72h_count,
    h.out_48h_incl_this,
    h.out_48h_incl_this / nullif(rc.checks_prior_72h, 0)                         as out_48h_vs_recent_checks,
    -- A generous allowance for normal spending: a full week of the account's trailing 90-day outflow (excludes
    -- today). Payroll and vendor runs are lumpy, so two days' average would be exceeded on every payroll day.
    coalesce(d.baseline_monthly_outflow, 0) / 30.4 * 7                           as normal_week_outflow,
    -- Share of the fresh check money that left ON TOP of that allowance, between 0 and 1.
    least(1, greatest(0, h.out_48h_incl_this - coalesce(d.baseline_monthly_outflow, 0) / 30.4 * 7)
             / nullif(rc.checks_prior_72h, 0))                                   as excess_out_48h_vs_recent_checks,
    h.prior_payments_to_payee,
    h.prior_payments_to_payee = 0                                                as is_first_payment_to_payee,
    h.payee_median_last6,
    h.amount / nullif(h.payee_median_last6, 0)                                   as amount_vs_payee_median,
    h.amount_band > coalesce(h.max_prior_amount_band, -1)                        as is_first_time_amount_band,
    h.seq_on_bank_details = 1                                                    as is_first_payment_to_bank_details,
    e.last_payee_event_type = 'bank_details_changed'                             as bank_details_were_changed,
    case when e.last_payee_event_type = 'bank_details_changed'
         then date_diff('second', e.last_payee_event_time, h.txn_time) / 86400.0 end as days_since_bank_details_change
from payment_history as h
join {{ ref('stg_businesses') }} as b using (business_id)
left join {{ ref('stg_payees') }} as py using (payee_id)
left join recent_checks as rc using (txn_id)
left join last_payee_event as e using (txn_id)
left join {{ ref('feat_business_daily') }} as d
    on d.business_id = h.business_id and d.activity_date = h.txn_date
