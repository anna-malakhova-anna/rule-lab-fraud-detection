select payee_event_id, payee_id, event_time, event_type, bank_details_id
from {{ source('raw', 'payee_events') }}
