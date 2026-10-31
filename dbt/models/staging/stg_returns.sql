select return_id, txn_id, return_time, return_reason
from {{ source('raw', 'returns') }}
