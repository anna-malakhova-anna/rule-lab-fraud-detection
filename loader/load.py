"""Load generated parquet into the warehouse: data/raw -> schema raw, data/answer_key -> schema answer_key.

Raw tables are loaded exactly as written. The answer key lives in its own schema; only dbt models under
models/backtest/ may read it (scripts/check_answer_key_isolation.py enforces this).
"""
from __future__ import annotations

from scripts.common import DB, ROOT, connect


def main() -> None:
    DB.parent.mkdir(exist_ok=True)
    con = connect(read_only=False)
    for schema, folder in (("raw", "raw"), ("answer_key", "answer_key")):
        con.execute(f"create schema if not exists {schema}")
        for f in sorted((ROOT / "data" / folder).glob("*.parquet")):
            con.execute(f"create or replace table {schema}.{f.stem} as select * from read_parquet('{f}')")
            n = con.execute(f"select count(*) from {schema}.{f.stem}").fetchone()[0]
            print(f"{schema}.{f.stem}: {n:,} rows")
    con.close()


if __name__ == "__main__":
    main()
