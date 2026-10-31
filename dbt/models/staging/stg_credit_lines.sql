select line_id, business_id, opened_at, initial_limit
from {{ source('raw', 'credit_lines') }}
