#!/usr/bin/env python3
"""
anonymize_export.py — run ONCE locally, before committing.

Produces the two files the public repo ships:
    data/pronoun_cell_counts.csv   (reproduces every model; no names, no poem text)
    data/author_meta.csv           (author_id, in_ukraine_2022, language; no names)

and one file it MUST NOT ship (gitignored):
    data/name_crosswalk.csv        (author_id -> real name; keep local only)

It is deliberately a *scrubber*: point --counts at whatever per-poem cell-count
export your Q1 pipeline produces, and it (a) replaces `author` with a stable
`author_id`, and (b) drops every free-text / name-bearing / source column, so
nothing identifying can leak even if the input schema changes.

Review the printed audit (esp. the in_ukraine mapping) before trusting output.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

# Columns that must never reach the public CSV, matched case-insensitively by substring.
DROP_SUBSTRINGS = (
    "text", "notes", "reference", "alias", "facebook",
    "birth", "provenance", "source", "name",  # 'name' last so 'author' is handled explicitly
    "region", "url", "fullname",
)
KEEP_ALWAYS = {"author_id", "poem_id", "year", "period_post", "cell",
               "k", "count", "n", "exposure_n_stanzas", "exposure_n_tokens",
               "language", "language_corpus_p1", "in_ukraine_2022"}

# region_jan2022 values that count as "remained in Ukraine after Feb 2022".
# Extend this set after reading the printed audit of your covariates file.
UKRAINE_REGION_TOKENS = {
    "kyiv", "lviv", "kharkiv", "odesa", "odessa", "dnipro", "vinnytsia",
    "west_ukraine", "east_ukraine", "south_ukraine", "north_ukraine",
    "central_ukraine", "ukraine",
}


def stable_id(name: str, n_digits: int = 2) -> str:
    """Deterministic opaque id from the name (so re-runs are stable)."""
    h = hashlib.sha256(name.strip().encode("utf-8")).hexdigest()
    return "A" + str(int(h, 16) % (10 ** n_digits)).zfill(n_digits)


def build_crosswalk(authors: list[str]) -> dict[str, str]:
    """Map each real name to A01..A33 in a stable, collision-checked way."""
    ids: dict[str, str] = {}
    used: set[str] = set()
    for name in sorted(set(a.strip() for a in authors)):
        cid = stable_id(name)
        salt = 0
        while cid in used:                      # resolve the rare hash collision
            salt += 1
            cid = stable_id(f"{name}#{salt}")
        used.add(cid)
        ids[name] = cid
    return ids


def in_ukraine_flag(region_value: object) -> int:
    s = str(region_value).strip().lower()
    return int(any(tok in s for tok in UKRAINE_REGION_TOKENS))


def scrub_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = []
    for col in df.columns:
        lc = col.lower()
        if col in KEEP_ALWAYS:
            keep.append(col)
        elif any(sub in lc for sub in DROP_SUBSTRINGS):
            continue                            # drop name/text/source columns
        else:
            keep.append(col)                    # numeric/structural columns survive
    return df[keep]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", type=Path, required=True,
                    help="Per-poem cell-count CSV (must have an 'author' column).")
    ap.add_argument("--covariates", type=Path, required=True,
                    help="author_covariates.csv (LOCAL ONLY; used to derive in_ukraine + language).")
    ap.add_argument("--outdir", type=Path, default=Path("data"))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv(args.counts)
    cov = pd.read_csv(args.covariates)
    if "author" not in counts.columns:
        raise SystemExit("--counts has no 'author' column; point it at the per-poem export.")

    crosswalk = build_crosswalk(counts["author"].astype(str).tolist())

    # 1) public counts: attach id, drop names/text, drop the raw name column
    counts = counts.copy()
    counts["author_id"] = counts["author"].astype(str).str.strip().map(crosswalk)
    counts = scrub_columns(counts.drop(columns=["author"]))
    counts_path = args.outdir / "pronoun_cell_counts.csv"
    counts.to_csv(counts_path, index=False)

    # 2) public author meta: id, in_ukraine_2022, primary language — nothing else
    region_col = next((c for c in cov.columns if c.lower() == "region_jan2022"), None)
    lang_col = next((c for c in cov.columns if "language_corpus_p1" in c.lower()), None)
    meta = pd.DataFrame({"author_name": cov["author"].astype(str).str.strip()})
    meta["author_id"] = meta["author_name"].map(crosswalk)
    meta = meta.dropna(subset=["author_id"])    # roster authors only
    meta["in_ukraine_2022"] = cov[region_col].map(in_ukraine_flag) if region_col else pd.NA
    meta["language"] = cov[lang_col] if lang_col else pd.NA
    audit = meta[["author_name", "author_id", "in_ukraine_2022", "language"]].copy()
    meta.drop(columns=["author_name"]).to_csv(args.outdir / "author_meta.csv", index=False)

    # 3) private crosswalk — gitignored, never shipped
    pd.DataFrame(
        sorted(crosswalk.items()), columns=["author_name", "author_id"]
    ).to_csv(args.outdir / "name_crosswalk.csv", index=False)

    print(f"wrote {counts_path}  ({len(counts)} rows, {counts['author_id'].nunique()} authors)")
    print(f"wrote {args.outdir/'author_meta.csv'}  and  {args.outdir/'name_crosswalk.csv'} (PRIVATE)")
    print("\n--- AUDIT: verify in_ukraine_2022 before trusting it ---")
    print(audit.to_string(index=False))
    print("\nReminder: confirm name_crosswalk.csv is gitignored and NOT staged.")


if __name__ == "__main__":
    main()
