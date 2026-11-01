-- Transactions that ARE the loss if nothing stops them (withdrawals of bad-check money, stolen vendor payments).
-- is_instant: the money left in seconds, so only an alert BEFORE it can stop it (ADR-021).
select ft.case_id, ft.txn_id, t.txn_time, ft.loss_amount, t.is_instant
from {{ source('answer_key', 'fraud_txns') }} as ft
join {{ ref('stg_transactions') }} as t using (txn_id)
where ft.role = 'loss'
