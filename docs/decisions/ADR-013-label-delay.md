# ADR-013: Labels arrive late, and some never

**Decision.** Each case gets a `label_known_at` date: case end plus a delay drawn per fraud type, or no date
at all for cases the bank never confirms.

| Fraud type | Delay after case end | Never confirmed |
|---|---|---|
| Check deposit fraud | 0 to 3 days (the return is the label) | 2% |
| BEC | 1 to 5 days | 3% |
| Shell | 5 to 30 days | 10% |
| Mule | 14 to 120 days (recall requests) | 20% |
| Account takeover | 0 to 2 days (the owner reports it) | 2% |
| ACH return fraud | 0 to 5 days | 5% |

**Where it is used.**
- **Tuning** sees only the cases known by the end of month 12. An alert on a case not yet confirmed counts
  as an alert on a good customer, as it would have at the time (`bt_sweep_metrics_known`).
- **Monitoring** reports precision as known 30 days after each week next to the eventual precision
  (`bt_monitoring_precision`).
- **The final champion/challenger grade uses all labels**, so it stays comparable with Phase 1. That is
  more than a real bank ever has. The site says so.
