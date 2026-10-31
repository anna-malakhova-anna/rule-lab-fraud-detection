-- Prevented loss can never exceed the loss at stake, and never be negative.
select * from {{ ref('bt_strategy_cases') }}
where loss_prevented < -0.005 or loss_prevented > loss_if_uncaught + 0.005
union all
select * from {{ ref('bt_sweep_cases') }}
where loss_prevented < -0.005 or loss_prevented > loss_if_uncaught + 0.005
