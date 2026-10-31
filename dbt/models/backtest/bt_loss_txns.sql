-- Transactions that ARE the loss if nothing stops them (withdrawals of bad-check money, stolen vendor payments).
select ft.case_id, ft.txn_id, t.txn_time, ft.loss_amount
from {{ source('answer_key', 'fraud_txns') }} as ft
join {{ ref('stg_transactions') }} as t using (txn_id)
where ft.role = 'loss'
