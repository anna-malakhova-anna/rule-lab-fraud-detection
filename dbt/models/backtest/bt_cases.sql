-- The planted fraud cases, with the period they start in and when the bank learns about them.
-- Reads the answer key: backtest only.
select
    c.case_id,
    c.business_id,
    c.typology,
    c.variant,
    c.ring_id,
    c.account_is_fraudulent,
    -- First-party fraud: the customer is the fraudster, so after the scheme starts their account is not a
    -- "good customer" any more. Account takeover and BEC victims stay good customers throughout.
    c.typology in ('check_deposit_fraud', 'synthetic_shell', 'money_mule', 'ach_return_fraud') as is_first_party,
    c.case_start,
    c.case_end,
    c.label_known_at,                                 -- null: the bank never confirms it (ADR-013)
    c.loss_if_uncaught,
    case when cast(c.case_start as date) < {{ window_value('train_end') }} then 'train' else 'test' end as period
from {{ source('answer_key', 'fraud_cases') }} as c
