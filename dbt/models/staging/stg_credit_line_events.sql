-- Line opened, increase requested and granted, payment missed, charged off. limit_after is set on opened and
-- increase events; balance on missed payments and charge-offs.
select credit_event_id, line_id, business_id, event_time, event_type, limit_after, balance
from {{ source('raw', 'credit_line_events') }}
