#!/usr/bin/env python3
"""
anonymize_export.py — run ONCE locally, before committing.

Produces the two files the public repo ships:
    data/pronoun_cell_counts.csv   (reproduces every model; no names, no poem text)
    data/author_meta.csv           (author_id, in_ukraine_2022, language; no names)

and one file it MUST NOT ship (gitignored):
    data/name_crosswalk.csv        (author_id -> real name; keep local only)

Point --counts at ``q1_poem_unit_cell_counts_12.csv`` from the Q1 pipeline
(already excludes translations/reposts/Crimean Tatar). Pass --roster to restrict
to the paper's modeled author set (33 authors). counts, meta, and crosswalk are
always written in one run so author_id spaces stay aligned.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DROP_SUBSTRINGS = (
    "text", "notes", "reference", "alias", "facebook",
    "birth", "provenance", "source", "name",
    "region", "url", "fullname",
)

# Paper modeling columns only (no 3sg/3pl; no free text).
PUBLIC_COUNT_COLUMNS = (
    "poem_id",
    "author_id",
    "1sg",
    "1pl",
    "2sg",
    "2pl_vy_polite_singular",
    "2pl_vy_true_plural",
    "2pl",
    "n_total",
    "exposure_n_stanzas",
    "exposure_n_stanza_index_max",
    "exposure_n_tokens",
    "exposure_n_finite_verbs",
    "exposure_n_finite_verbs_excl_imperative",
    "min_stanzas",
    "min_tokens",
    "include_in_offset_models",
    "include_in_fv_offset_models",
    "include_in_fv_excl_imp_offset_models",
    "language_clean",
    "year_int",
    "period3",
)

UKRAINE_REGION_TOKENS = {
    "kyiv", "lviv", "kharkiv", "odesa", "odessa", "dnipro", "vinnytsia",
    "west_ukraine", "east_ukraine", "south_ukraine", "north_ukraine",
    "central_ukraine", "ukraine",
}


def sequential_ids(authors: list[str]) -> dict[str, str]:
    """Map sorted real names to A01..An (contiguous, roster-sized)."""
    return {
        name: f"A{idx:02d}"
        for idx, name in enumerate(sorted(set(a.strip() for a in authors)), start=1)
    }


def in_ukraine_flag(region_value: object) -> int:
    s = str(region_value).strip().lower()
    return int(any(tok in s for tok in UKRAINE_REGION_TOKENS))


def load_roster_authors(path: Path) -> set[str]:
    roster = pd.read_csv(path, low_memory=False)
    if "author" in roster.columns:
        key = "author"
    elif "author_name" in roster.columns:
        key = "author_name"
    else:
        raise SystemExit(f"{path} needs an 'author' or 'author_name' column")
    if "included" in roster.columns:
        roster = roster.loc[roster["included"].astype(bool)]
    return set(roster[key].astype(str).str.strip())


def select_public_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in PUBLIC_COUNT_COLUMNS if c in df.columns]
    return df[cols].copy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", type=Path, required=True,
                    help="q1_poem_unit_cell_counts_12.csv (must have 'author').")
    ap.add_argument("--covariates", type=Path, required=True,
                    help="author_covariates.csv (LOCAL ONLY; in_ukraine + language).")
    ap.add_argument("--roster", type=Path, default=None,
                    help="Optional roster CSV; keep only these authors before anonymizing.")
    ap.add_argument("--outdir", type=Path, default=Path("data"))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv(args.counts, low_memory=False)
    cov = pd.read_csv(args.covariates, low_memory=False)
    if "author" not in counts.columns:
        raise SystemExit("--counts has no 'author' column")

    if args.roster is not None:
        roster_authors = load_roster_authors(args.roster)
        counts = counts[counts["author"].astype(str).str.strip().isin(roster_authors)].copy()
        cov = cov[cov["author"].astype(str).str.strip().isin(roster_authors)].copy()

    authors_in_counts = counts["author"].astype(str).str.strip().tolist()
    crosswalk = sequential_ids(authors_in_counts)

    counts = counts.copy()
    counts["author_id"] = counts["author"].astype(str).str.strip().map(crosswalk)
    if counts["author_id"].isna().any():
        raise SystemExit("author_id mapping failed — check roster/counts alignment")
    counts = select_public_columns(counts.drop(columns=["author"]))
    counts_path = args.outdir / "pronoun_cell_counts.csv"
    counts.to_csv(counts_path, index=False)

    region_col = next((c for c in cov.columns if c.lower() == "region_jan2022"), None)
    lang_col = next((c for c in cov.columns if "language_corpus_p1" in c.lower()), None)
    meta = pd.DataFrame({"author_name": cov["author"].astype(str).str.strip()})
    meta["author_id"] = meta["author_name"].map(crosswalk)
    meta = meta.dropna(subset=["author_id"])
    meta["in_ukraine_2022"] = cov[region_col].map(in_ukraine_flag) if region_col else pd.NA
    meta["language"] = cov[lang_col] if lang_col else pd.NA
    audit = meta[["author_name", "author_id", "in_ukraine_2022", "language"]].copy()
    meta.drop(columns=["author_name"]).to_csv(args.outdir / "author_meta.csv", index=False)

    pd.DataFrame(sorted(crosswalk.items()), columns=["author_name", "author_id"]).to_csv(
        args.outdir / "name_crosswalk.csv", index=False
    )

    # Anonymized roster for downstream scripts (no names).
    if args.roster is not None:
        roster = pd.read_csv(args.roster, low_memory=False)
        if "included" not in roster.columns:
            roster = roster.assign(included=True)
        keep = [c for c in ("author", "author_id", "n_p1", "n_p2", "min_per_period", "total", "included") if c in roster.columns]
        if "author" in roster.columns:
            roster = roster[keep + [c for c in roster.columns if c not in keep and c != "author"]].copy()
            roster["author_id"] = roster["author"].astype(str).str.strip().map(crosswalk)
            roster = roster.dropna(subset=["author_id"])
            public_roster_cols = [c for c in ("author_id", "n_p1", "n_p2", "min_per_period", "total", "included") if c in roster.columns]
            roster[public_roster_cols].to_csv(args.outdir / "roster_v1_frozen.csv", index=False)

    print(f"wrote {counts_path}  ({len(counts)} rows, {counts['author_id'].nunique()} authors)")
    print(f"wrote {args.outdir/'author_meta.csv'}  and  {args.outdir/'name_crosswalk.csv'} (PRIVATE)")
    print("\n--- AUDIT: verify in_ukraine_2022 before trusting it ---")
    print(audit.to_string(index=False))
    print("\nReminder: confirm name_crosswalk.csv is gitignored and NOT staged.")


if __name__ == "__main__":
    main()
