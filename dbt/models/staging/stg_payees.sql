select payee_id, business_id, payee_type, payee_name, created_at
from {{ source('raw', 'payees') }}
