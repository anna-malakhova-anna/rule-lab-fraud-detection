-- The sweep as the bank could have measured it when tuning: labels known by the end of month 12 only.
-- Fraud confirmed later looks like a good customer here, exactly as it would have at the time.
{{ strategy_metrics(ref('bt_sweep_graded'), ref('bt_sweep_cases_known'), ref('bt_sweep_strategies'),
                    label_as_of=window_value('train_end')) }}
