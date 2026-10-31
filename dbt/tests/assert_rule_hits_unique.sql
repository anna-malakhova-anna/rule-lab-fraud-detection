-- A rule hits a transaction at most once.
select rule_id, entity_id, count(*) from {{ ref('rule_hits') }} group by 1, 2 having count(*) > 1
