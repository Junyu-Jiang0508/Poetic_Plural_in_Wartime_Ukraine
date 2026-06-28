#!/usr/bin/env python3
"""Export author-free collocation counts for the public replication repo."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Local collocations_by_cell_period.csv (from collocations.py).",
    )
    ap.add_argument("--output", type=Path, default=Path("data/collocations_pronoun_head.csv"))
    args = ap.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    required = {"language", "cell", "period", "head_lemma", "cooccurrence"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"input missing columns: {sorted(missing)}")

    out = (
        df.groupby(["language", "cell", "period", "head_lemma"], as_index=False)["cooccurrence"]
        .sum()
        .rename(columns={"cooccurrence": "cooccurrence_count"})
        .sort_values(["language", "cell", "period", "cooccurrence_count"], ascending=[True, True, True, False])
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"wrote {args.output}  ({len(out)} rows)")


if __name__ == "__main__":
    main()
