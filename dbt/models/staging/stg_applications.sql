-- Onboarding applications, approved and declined. The email domain is split out because a shared BUSINESS
-- domain links applicants while a shared free-mail domain (gmail and the like) links nobody.
select
    application_id,
    business_id,
    applied_at,
    decision,
    industry,
    stated_monthly_revenue,
    incorporation_date,
    state,
    applicant_name,
    email,
    lower(split_part(email, '@', 2))                                   as email_domain,
    lower(split_part(email, '@', 2)) in ('gmail.com', 'yahoo.com', 'hotmail.com')  as is_free_email_domain,
    phone,
    address,
    device_id
from {{ source('raw', 'applications') }}
