"""Paths and small helpers shared by scripts."""
from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "lab.duckdb"
CONFIG = ROOT / "config"


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG / name).read_text())


def connect(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB), read_only=read_only)
