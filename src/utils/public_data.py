"""Load anonymized tables shipped in ``data/`` for public replication."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.workspace import (
    canonical_author_meta_csv,
    canonical_collocations_csv,
    canonical_poem_cell_counts_csv,
    canonical_roster_csv,
    repository_root,
)

PAPER_COUNT_COLUMNS = (
    "poem_id",
    "author_id",
    "author",
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


def _ensure_author_alias(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "author_id" in out.columns and "author" not in out.columns:
        out["author"] = out["author_id"].astype(str)
    elif "author" in out.columns and "author_id" not in out.columns:
        out["author_id"] = out["author"].astype(str)
    return out


def load_shipped_poem_table(path: Path | None = None) -> pd.DataFrame:
    """Return the poem-level count table from ``data/pronoun_cell_counts.csv``."""
    p = (path or canonical_poem_cell_counts_csv()).resolve()
    df = pd.read_csv(p, low_memory=False)
    df = _ensure_author_alias(df)
    df["poem_id"] = df["poem_id"].astype(str).str.strip()
    if "year_int" in df.columns:
        df["year_int"] = pd.to_numeric(df["year_int"], errors="coerce")
    if "n_total" not in df.columns:
        count_cols = [c for c in ("1sg", "1pl", "2sg", "2pl_vy_true_plural", "2pl") if c in df.columns]
        df["n_total"] = df[count_cols].sum(axis=1)
    for flag in (
        "include_in_offset_models",
        "include_in_fv_offset_models",
        "include_in_fv_excl_imp_offset_models",
    ):
        if flag not in df.columns:
            df[flag] = True
    return df


def load_shipped_roster(path: Path | None = None) -> pd.DataFrame:
    p = (path or canonical_roster_csv()).resolve()
    df = pd.read_csv(p, low_memory=False)
    return _ensure_author_alias(df)


def load_shipped_collocations(path: Path | None = None) -> pd.DataFrame:
    p = (path or canonical_collocations_csv()).resolve()
    df = pd.read_csv(p, low_memory=False)
    if "cooccurrence_count" in df.columns and "cooccurrence" not in df.columns:
        df = df.rename(columns={"cooccurrence_count": "cooccurrence"})
    if "deprel" not in df.columns:
        df["deprel"] = "merged"
    return df


def load_shipped_author_meta(path: Path | None = None) -> pd.DataFrame:
    p = (path or canonical_author_meta_csv()).resolve()
    df = pd.read_csv(p, low_memory=False)
    return _ensure_author_alias(df)


def is_shipped_poem_table(path: Path) -> bool:
    """True when ``path`` looks like the public poem-level counts CSV."""
    try:
        resolved = path.resolve()
        shipped = canonical_poem_cell_counts_csv(repository_root()).resolve()
        return resolved == shipped or resolved.name == shipped.name
    except OSError:
        return path.name == "pronoun_cell_counts.csv"
