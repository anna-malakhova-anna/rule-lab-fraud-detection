"""Fail if anything other than the backtest grader can see the answer key.

Two checks:
  1. Lineage (dbt/target/manifest.json): every dbt model, seed or snapshot outside models/backtest/ must have no answer_key source
     anywhere upstream. Catches a rule or feature that refs a backtest model, or calls a backtest macro.
  2. Text: no model outside models/backtest/, no macro other than macros/backtest.sql, and no Python outside the
     generator, loader and this check may mention the answer key at all.

  uv run python -m scripts.check_answer_key_isolation
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from scripts.common import ROOT

MANIFEST = ROOT / "dbt" / "target" / "manifest.json"
SOURCE = "answer_key"
ALLOWED_MODEL_DIR = "models/backtest/"
ALLOWED_TEXT = {
    "dbt/models/sources.yml",
    "dbt/macros/backtest.sql",
    "generator/main.py",
    "loader/load.py",
    "scripts/check_answer_key_isolation.py",
}
PATTERN = re.compile(r"answer_key")


def lineage_leaks(manifest: dict) -> list[tuple[str, str]]:
    nodes = {**manifest["nodes"], **manifest["sources"]}

    def upstream(node_id: str, seen: set) -> set:
        for parent in nodes.get(node_id, {}).get("depends_on", {}).get("nodes", []):
            if parent not in seen:
                seen.add(parent)
                upstream(parent, seen)
        return seen

    leaks = []
    for node_id, node in manifest["nodes"].items():
        path = node["original_file_path"].replace("\\", "/")
        # Data tests produce no rows anything can read, so a test on a backtest model cannot leak into a rule.
        if path.startswith(ALLOWED_MODEL_DIR) or node.get("resource_type") == "test":
            continue
        for up in upstream(node_id, set()):
            src = manifest["sources"].get(up)
            if src and src["source_name"] == SOURCE:
                leaks.append((path, up))
    return sorted(set(leaks))


def text_leaks(root: Path = ROOT) -> list[str]:
    files = list((root / "dbt" / "models").rglob("*.sql")) + list((root / "dbt" / "models").rglob("*.yml"))
    files += list((root / "dbt" / "macros").rglob("*.sql"))
    files += [p for d in ("generator", "loader", "scripts") for p in (root / d).rglob("*.py")]
    out = []
    for p in files:
        rel = p.relative_to(root).as_posix()
        if rel in ALLOWED_TEXT or rel.startswith("dbt/" + ALLOWED_MODEL_DIR):
            continue
        if PATTERN.search(p.read_text()):
            out.append(rel)
    return sorted(out)


def main() -> int:
    if not MANIFEST.exists():
        print(f"{MANIFEST} not found: run `dbt parse` first", file=sys.stderr)
        return 2
    leaks = lineage_leaks(json.loads(MANIFEST.read_text()))
    texts = text_leaks()
    for path, src in leaks:
        print(f"ANSWER KEY LEAK (lineage): {path} <- {src}", file=sys.stderr)
    for path in texts:
        print(f"ANSWER KEY LEAK (text): {path} mentions the answer key", file=sys.stderr)
    if leaks or texts:
        return 1
    print("answer key isolation: OK (only models/backtest/ reads it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
