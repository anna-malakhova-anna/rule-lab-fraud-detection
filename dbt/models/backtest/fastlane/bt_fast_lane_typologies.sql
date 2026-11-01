-- Which fraud gets through when established, clean businesses are softened or cleared (module E): fraud dollars
-- prevented by fraud type, against the challenger. Takeovers, vendor-impersonation scams and credit bust-outs
-- hit established accounts, which is why the fast lane only softens the rules aimed at a fraudster's own account.
select
    s.strategy_id,
    s.period,
    s.typology,
    sum(s.loss_if_uncaught)                       as loss_if_uncaught,
    sum(s.loss_prevented)                         as loss_prevented,
    sum(base.loss_prevented) - sum(s.loss_prevented) as fraud_let_through
from {{ ref('bt_strategy_cases') }} as s
join {{ ref('bt_strategy_cases') }} as base
    on base.strategy_id = 'challenger' and base.case_id = s.case_id
where s.strategy_id like 'fast_lane%' and s.period in ('train', 'test')
group by s.strategy_id, s.period, s.typology
