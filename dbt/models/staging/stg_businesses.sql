select
    b.business_id,
    b.legal_name,
    b.industry,
    b.size_band,
    b.incorporation_date,
    b.state,
    b.stated_monthly_revenue,
    a.open_date
from {{ source('raw', 'businesses') }} as b
join {{ source('raw', 'accounts') }} as a
    on a.business_id = b.business_id and a.account_type = 'operating'
