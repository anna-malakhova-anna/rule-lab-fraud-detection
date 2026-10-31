-- The threshold sweep: each rule alone at each cutoff, per period. The trade-off curves are drawn from this.
{{ strategy_metrics(ref('bt_sweep_graded'), ref('bt_sweep_cases'), ref('bt_sweep_strategies')) }}
