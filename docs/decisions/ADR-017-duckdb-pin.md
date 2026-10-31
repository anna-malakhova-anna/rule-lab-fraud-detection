# ADR-017: Pin DuckDB below 2.0

**Problem.** DuckDB 2.0.0 (released 2026-10-21) intermittently failed `feat_outbound_payments` with an internal
error: "dict-surviving join: narrowed column ... build pipeline is not single-source". It failed 4 of 6 runs with
default settings and 6 of 6 when DuckDB ran single-threaded. The model's SQL had not changed, and it never failed
on the same data before 2.0.

**Decision.** Pin `duckdb>=1.5.6,<2` in `pyproject.toml` (1.5.6 was released 2026-09-28). With it, the same model
passed 6 of 6 runs, and the full build and tests pass.

**Revisit** when a 2.0.x patch release fixes the join. Then remove the upper bound and run `make all` a few times.
