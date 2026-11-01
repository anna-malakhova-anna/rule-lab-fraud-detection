-- Outbound payments made within 7 days after a scored new-device login or contact change on the same business:
-- the payment-side use of the device and contact vendors. One row per (payment, call point), so each call
-- strategy can keep only the call points it would have paid for.
select
    c.vendor,
    c.call_point,
    c.call_point_id,
    c.risk_gated_call,
    c.score,
    p.txn_id,
    p.business_id,
    p.txn_time,
    p.txn_type,
    p.amount
from {{ ref('vnd_call_points') }} as c
join {{ ref('feat_outbound_payments') }} as p
    on  p.business_id = c.business_id
    and p.txn_time >= c.called_at
    and p.txn_time <  c.called_at + interval 7 day
where c.call_point in ('new_device_login', 'contact_change')
  and c.covered
  and p.txn_type <> 'payroll'
