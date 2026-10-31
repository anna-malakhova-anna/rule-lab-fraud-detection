-- The planted fraud cases, with the period they start in. Reads the answer key: backtest only.
select
    c.case_id,
    c.business_id,
    c.typology,
    c.variant,
    c.account_is_fraudulent,
    c.case_start,
    c.case_end,
    c.loss_if_uncaught,
    case when cast(c.case_start as date) < {{ window_value('train_end') }} then 'train' else 'test' end as period
from {{ source('answer_key', 'fraud_cases') }} as c
