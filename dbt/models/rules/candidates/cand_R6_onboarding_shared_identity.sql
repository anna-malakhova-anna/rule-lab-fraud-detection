-- Approved applications, scored by how much identity they share with any ONE earlier applicant (a bookkeeper's
-- device alone, or a co-working address alone, scores 1; a ring sharing device, phone and address scores 3+),
-- plus one point for a business incorporated only weeks before applying.
select
    'R6_onboarding_shared_identity'           as rule_id,
    application_id                            as txn_id,
    business_id,
    applied_at                                as event_time,
    'application'                             as txn_type,
    0.0                                       as amount,
    cast(max_shared_with_one
      + case when days_incorporated <= {{ rule_param('R6_onboarding_shared_identity', 'young_incorporation_days') }}
             then 1 else 0 end as double)     as score,
    printf('shares %s with an earlier applicant; %d linked applications (%d declined); incorporated %d days before applying',
           coalesce(most_shared_attributes, 'nothing'), linked_applications, linked_declined_applications, days_incorporated) as detail
from {{ ref('feat_applications') }}
where decision = 'approved'
