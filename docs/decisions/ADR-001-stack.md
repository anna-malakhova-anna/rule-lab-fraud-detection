# ADR-001: Stack and layout

**Decision.** Python generates the synthetic bank (seed 42) and writes parquet. A loader puts it in DuckDB
as-is. dbt does everything analytical: features, rules and the backtest. Python is used only where SQL is
awkward: the bootstrap, rendering the README and memo tables, and the results page.

**Why.** I want the SQL to show the reasoning. Thresholds and assumptions live in YAML (`config/`), and the
YAML is exported to dbt seeds. That way a sweep varies config, not code.

**DuckDB-specific pieces** (to swap if this moves to another warehouse): `printf` in rule reasons,
`arg_max`, `string_split`/`unnest`, `qualify`, `generate_series`, and `RANGE` window frames with intervals.
