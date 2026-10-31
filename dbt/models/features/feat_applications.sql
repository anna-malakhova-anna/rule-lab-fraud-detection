-- One row per application, with links to EARLIER applications (approved or declined) that share an identity
-- attribute. Four equi-joins (one per attribute) unioned, then folded to one row per pair, so a pair sharing
-- device AND phone AND address counts as one linked applicant with three shared attributes.
with apps as (
    select * from {{ ref('stg_applications') }}
),

shared_pairs as (
    select a.application_id, p.application_id as other_id, 'device' as attribute
    from apps as a join apps as p on p.device_id = a.device_id and p.applied_at < a.applied_at
    union all
    select a.application_id, p.application_id, 'phone'
    from apps as a join apps as p on p.phone = a.phone and p.applied_at < a.applied_at
    union all
    select a.application_id, p.application_id, 'address'
    from apps as a join apps as p on p.address = a.address and p.applied_at < a.applied_at
    union all
    -- Only business domains link people; thousands of applicants share a free-mail domain.
    select a.application_id, p.application_id, 'email_domain'
    from apps as a join apps as p
        on p.email_domain = a.email_domain and p.applied_at < a.applied_at and not a.is_free_email_domain
),

per_pair as (
    select application_id, other_id, count(distinct attribute) as n_shared, string_agg(distinct attribute, '+' order by attribute) as shared
    from shared_pairs
    group by application_id, other_id
),

per_app as (
    select
        pp.application_id,
        count(*)                                                     as linked_applications,
        count(*) filter (where o.decision = 'declined')              as linked_declined_applications,
        max(pp.n_shared)                                             as max_shared_with_one,
        arg_max(pp.shared, pp.n_shared)                              as most_shared_attributes,
        count(*) filter (where pp.shared like '%device%')            as linked_by_device,
        count(*) filter (where pp.shared like '%address%')           as linked_by_address
    from per_pair as pp
    join apps as o on o.application_id = pp.other_id
    group by pp.application_id
)

select
    a.application_id,
    a.business_id,
    a.applied_at,
    a.decision,
    a.industry,
    a.stated_monthly_revenue,
    date_diff('day', a.incorporation_date, cast(a.applied_at as date))  as days_incorporated,
    coalesce(p.linked_applications, 0)                                   as linked_applications,
    coalesce(p.linked_declined_applications, 0)                          as linked_declined_applications,
    coalesce(p.max_shared_with_one, 0)                                   as max_shared_with_one,
    p.most_shared_attributes,
    coalesce(p.linked_by_device, 0)                                      as linked_by_device,
    coalesce(p.linked_by_address, 0)                                     as linked_by_address
from apps as a
left join per_app as p using (application_id)
