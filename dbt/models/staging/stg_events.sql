select event_id, business_id, owner_id, event_time, event_type, device_id
from {{ source('raw', 'events') }}
