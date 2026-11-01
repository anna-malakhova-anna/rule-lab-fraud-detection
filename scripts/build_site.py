"""Build the static results site (site/) from the warehouse.

Every number comes from scripts/results.py. Charts are inline SVG (scripts/sitegen/charts.py): no third-party
scripts, fonts, images or logos (scripts/site_check.py refuses them). The output is deterministic, so the
committed site can be checked against a fresh build (tests/test_outputs.py).

  uv run python -m scripts.build_site [out_dir]
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from scripts import results as R
from scripts.common import ROOT
from scripts.sitegen.components import shell
from scripts.sitegen.pages import (
    fastlane,
    glossary,
    launch,
    limitations,
    monitoring,
    overview,
    riskops,
    rules,
    summaries,
    tradeoffs,
    types,
    vendors,
)

SITE = ROOT / "site"


def pages() -> dict[str, tuple[str, str, int]]:
    """published path -> (title, body html, folder depth)"""
    out = {
        "index.html": ("Overview", overview.overview(), 0),
        "tradeoffs.html": ("Trade-offs", tradeoffs.tradeoffs(), 0),
        "rules.html": ("Rules", rules.rules(), 0),
        "types.html": ("Fraud types", types.types_index(), 0),
        "riskops.html": ("Risk Ops", riskops.riskops(), 0),
        "launch.html": ("Launch review", launch.launch(), 0),
        "vendors.html": ("Vendors", vendors.vendors(), 0),
        "fastlane.html": ("Fast lane", fastlane.fastlane(), 0),
        "monitoring.html": ("Monitoring", monitoring.monitoring(), 0),
        "summaries.html": ("Case summaries", summaries.summaries(), 0),
        "limitations.html": ("How sure are we", limitations.limitations(), 0),
        "glossary.html": ("Glossary", glossary.glossary(), 0),
    }
    for key, label in R.TYPOLOGY_LABELS.items():
        out[f"types/{key}.html"] = (label, types.type_page(key), 1)
    return out


def build(out_dir: Path = SITE) -> int:
    shutil.rmtree(out_dir, ignore_errors=True)
    built = pages()
    for rel, (title, body, depth) in built.items():
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(shell(title, body, depth, rel))
    return len(built)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE
    print(f"wrote {build(out)} pages to {out}")


if __name__ == "__main__":
    main()
