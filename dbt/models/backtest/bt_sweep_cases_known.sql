-- Sweep case outcomes using only the cases the bank had confirmed by the end of the training months (ADR-013).
{{ case_outcomes(ref('bt_sweep_graded'), ref('bt_sweep_strategies'), label_as_of=window_value('train_end')) }}
