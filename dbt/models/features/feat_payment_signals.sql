-- Extra point-in-time signals for each outbound payment, for the Phase 2 rules:
--   account takeover: the latest login from a never-seen device in the 7 days before, a contact change since
--                     then, and whether the payee was added after that login;
--   mules:            first-time senders paying in over the last 14 days, and how much went back out;
--   ACH debits:       money pulled in by ACH debit in the last 5 days (still returnable).
with payments as (
    select * from {{ ref('feat_outbound_payments') }}
),

-- A device's first login on a business is a "new device" event.
logins as (
    select
        business_id, event_time, device_id,
        row_number() over (partition by business_id, device_id order by event_time, event_id) = 1 as is_new_device
    from {{ ref('stg_events') }}
    where event_type = 'login'
),

latest_new_device as (
    select p.txn_id, l.event_time as new_device_login_at
    from payments as p
    join logins as l
        on  l.business_id = p.business_id
        and l.is_new_device
        and l.event_time <= p.txn_time
        and l.event_time >  p.txn_time - interval 7 day
    qualify row_number() over (partition by p.txn_id order by l.event_time desc) = 1
),

contact_change as (
    select n.txn_id, count(*) as contact_changes_since_new_device
    from latest_new_device as n
    join payments as p using (txn_id)
    join {{ ref('stg_events') }} as e
        on  e.business_id = p.business_id
        and e.event_type in ('email_changed', 'phone_changed')
        and e.event_time between n.new_device_login_at and p.txn_time
    group by n.txn_id
),

-- First time each counterparty paid this business, by any inbound channel.
first_paid as (
    select business_id, counterparty_id, min(txn_time) as first_paid_at
    from {{ ref('stg_transactions') }}
    where direction = 'in' and counterparty_id is not null
    group by business_id, counterparty_id
),

new_sender_inbound as (
    select t.business_id, t.txn_time, t.amount, t.counterparty_id
    from {{ ref('stg_transactions') }} as t
    join first_paid as f
        on f.business_id = t.business_id and f.counterparty_id = t.counterparty_id and f.first_paid_at = t.txn_time
    where t.txn_type in ('ach_in', 'wire_in')
),

fan_in as (
    select p.txn_id, count(distinct i.counterparty_id) as new_senders_14d, sum(i.amount) as new_sender_inbound_14d
    from payments as p
    join new_sender_inbound as i
        on  i.business_id = p.business_id
        and i.txn_time >  p.txn_time - interval 14 day
        and i.txn_time <= p.txn_time
    group by p.txn_id
),

ach_pulls as (
    select p.txn_id, sum(d.amount) as ach_debits_prior_5d
    from payments as p
    join {{ ref('stg_transactions') }} as d
        on  d.business_id = p.business_id
        and d.txn_type = 'ach_debit_in'
        and d.txn_time >  p.txn_time - interval 5 day
        and d.txn_time <= p.txn_time
    group by p.txn_id
)

select
    p.txn_id,
    p.business_id,
    p.txn_time,
    p.txn_type,
    p.amount,
    p.payee_id,
    p.payee_type,
    p.is_first_payment_to_payee,
    -- Account takeover sequence
    n.new_device_login_at,
    date_diff('second', n.new_device_login_at, p.txn_time) / 3600.0                as hours_since_new_device,
    coalesce(c.contact_changes_since_new_device, 0)                                as contact_changes_since_new_device,
    py.created_at >= n.new_device_login_at                                         as payee_added_after_new_device,
    -- Mule fan-in and sweep
    coalesce(f.new_senders_14d, 0)                                                  as new_senders_14d,
    coalesce(f.new_sender_inbound_14d, 0)                                           as new_sender_inbound_14d,
    sum(p.amount) over (partition by p.business_id order by p.txn_time
                        range between interval 14 day preceding and current row)  as out_14d_incl_this,
    -- ACH debits pulled in, measured like R1 measures checks: outflow above a normal week of spending
    coalesce(a.ach_debits_prior_5d, 0)                                              as ach_debits_prior_5d,
    p.out_48h_incl_this,
    p.normal_week_outflow,
    least(1, greatest(0, p.out_48h_incl_this - p.normal_week_outflow) / nullif(a.ach_debits_prior_5d, 0)) as excess_out_48h_vs_ach_debits
from payments as p
left join {{ ref('stg_payees') }} as py using (payee_id)
left join latest_new_device as n using (txn_id)
left join contact_change as c using (txn_id)
left join fan_in as f using (txn_id)
left join ach_pulls as a using (txn_id)
