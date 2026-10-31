-- One row per mobile check deposit, with point-in-time features: only information available when the check arrived.
with checks as (
    select txn_id, business_id, txn_time, txn_date, amount, counterparty_id
    from {{ ref('stg_transactions') }}
    where is_check_deposit
),

-- When did each payer first pay this business, by any inbound channel?
first_paid as (
    select business_id, counterparty_id, min(txn_time) as first_paid_at
    from {{ ref('stg_transactions') }}
    where direction = 'in' and counterparty_id is not null
    group by business_id, counterparty_id
),

checks_flagged as (
    select c.*, c.txn_time = f.first_paid_at as is_first_time_payer
    from checks as c
    join first_paid as f using (business_id, counterparty_id)
),

-- Self-join: distinct first-time payers among this business's check deposits in the 7 days up to and including this one.
new_payers as (
    select c.txn_id, count(distinct p.counterparty_id) as new_payers_7d
    from checks_flagged as c
    join checks_flagged as p
        on  p.business_id = c.business_id
        and p.is_first_time_payer
        and p.txn_time >  c.txn_time - interval 7 day
        and p.txn_time <= c.txn_time
    group by c.txn_id
),

-- Self-join: check money that arrived in the 72 hours before this one (still uncleared).
recent as (
    select c.txn_id, sum(p.amount) as other_checks_prior_72h, count(*) as other_checks_prior_72h_count
    from checks as c
    join checks as p
        on  p.business_id = c.business_id
        and p.txn_time >= c.txn_time - interval 72 hour
        and p.txn_time <  c.txn_time
    group by c.txn_id
),

data_start as (select min(txn_date) as first_data_date from {{ ref('stg_transactions') }}),

base as (
    select
        c.txn_id,
        c.business_id,
        c.txn_time,
        c.txn_date,
        c.amount,
        c.counterparty_id,
        c.is_first_time_payer,
        b.industry,
        b.stated_monthly_revenue,
        c.txn_date - b.open_date                                        as days_since_open,
        c.txn_date - greatest(b.open_date, ds.first_data_date)          as history_days,
        coalesce(np.new_payers_7d, 0)                                   as new_payers_7d,
        coalesce(r.other_checks_prior_72h, 0)                           as other_checks_prior_72h,
        coalesce(r.other_checks_prior_72h_count, 0)                     as other_checks_prior_72h_count,
        d.baseline_monthly_inflow,
        date_trunc('month', c.txn_date)                                 as txn_month
    from checks_flagged as c
    join {{ ref('stg_businesses') }} as b using (business_id)
    cross join data_start as ds
    left join new_payers as np using (txn_id)
    left join recent as r using (txn_id)
    left join {{ ref('feat_business_daily') }} as d
        on d.business_id = c.business_id and d.activity_date = c.txn_date
),

-- What is normal for the industry? Mean and spread of new_payers_7d per industry per month, applied to the
-- FOLLOWING month so a deposit is never compared with a distribution that includes itself.
industry_month as (
    select
        industry,
        txn_month + interval 1 month       as applies_to_month,
        avg(new_payers_7d)                 as industry_mean_new_payers_7d,
        stddev_samp(new_payers_7d)         as industry_sd_new_payers_7d
    from base
    group by industry, txn_month
)

select
    b.* exclude (txn_month),
    b.amount / nullif(b.baseline_monthly_inflow, 0)                                       as amount_vs_baseline,
    (b.new_payers_7d - im.industry_mean_new_payers_7d) / nullif(im.industry_sd_new_payers_7d, 0) as new_payers_7d_industry_z
from base as b
left join industry_month as im
    on im.industry = b.industry and im.applies_to_month = b.txn_month
