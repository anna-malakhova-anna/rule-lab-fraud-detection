-- Weekdays in the graded window, split into the training and test periods (ADR-002). Holidays are ignored.
select
    cast(d as date) as business_date,
    case when d < {{ window_value('train_end') }} then 'train' else 'test' end as period
from generate_series(cast({{ window_value('window_start') }} as timestamp),
                     cast({{ window_value('window_end') }} as timestamp) - interval 1 day,
                     interval 1 day) as g(d)
where dayofweek(d) between 1 and 5
