.PHONY: all setup generate load config build backtest summaries test site results isolation lint clean

PY  := uv run python
DBT := cd dbt && uv run dbt

# The one full build from an empty checkout: synthetic data -> warehouse -> rules -> backtest -> outputs -> tests.
all: generate load build backtest summaries results site test

setup:
	uv sync

# Synthetic bank (seed 42): raw files in data/raw, answer key in data/answer_key.
generate:
	$(PY) -m generator.main

load:
	$(PY) -m loader.load

# YAML config -> dbt seeds. YAML is the source of truth for thresholds and backtest assumptions.
config:
	$(PY) -m scripts.export_config

# Staging, features and rules (everything that does NOT read the answer key), then the backtest models.
build: config
	$(DBT) seed --profiles-dir . --full-refresh
	$(DBT) run --profiles-dir . --exclude path:models/backtest
	$(DBT) run --profiles-dir . --select path:models/backtest

# Threshold sweep and champion/challenger are dbt models (built above); this adds bootstrap ranges and the
# Risk Ops queue simulation (module A).
backtest:
	$(PY) -m scripts.bootstrap
	$(PY) -m scripts.queue_sim

# Case summaries for analysts, checked against their case data, and the guardrail's measured catch rate (module G).
summaries:
	$(PY) -m scripts.case_summaries

# README results table and the memo's numbers table, regenerated from the warehouse.
results:
	$(PY) -m scripts.render_results

site:
	$(PY) -m scripts.build_site
	$(PY) -m scripts.site_check

isolation:
	$(DBT) parse --profiles-dir .
	$(PY) -m scripts.check_answer_key_isolation

lint:
	uv run ruff check generator loader scripts tests

test: lint isolation
	$(DBT) test --profiles-dir .
	uv run pytest -q

clean:
	rm -rf data/raw/*.parquet data/answer_key/*.parquet warehouse/*.duckdb site dbt/target
