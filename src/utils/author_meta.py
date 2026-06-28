"""Anonymized author-level metadata for the public replication repo."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from utils.workspace import canonical_author_meta_csv, repository_root

log = logging.getLogger(__name__)

DEFAULT_META_PATH = repository_root() / "data" / "author_meta.csv"
SAFE_FOR_PERIOD_SLOPE_PREDICTORS: tuple[str, ...] = ("in_ukraine_2022", "language")


def is_covariate_missing(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    return s.eq("") | s.str.casefold().eq("unknown") | s.eq("nan")


def load_author_meta(path: Path | None = None, *, warn_on_missing: bool = True) -> pd.DataFrame:
    p = (path or canonical_author_meta_csv()).resolve()
    if not p.is_file():
        if warn_on_missing:
            log.warning("Author meta file %s not found.", p)
        return pd.DataFrame(columns=["author_id", "in_ukraine_2022", "language"])
    df = pd.read_csv(p, low_memory=False)
    if "author_id" not in df.columns:
        raise ValueError(f"{p} must contain author_id")
    return df


def merge_onto_poem_table(
    poem_df: pd.DataFrame,
    meta: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if meta is None:
        meta = load_author_meta()
    if meta.empty:
        return poem_df
    key = "author_id" if "author_id" in poem_df.columns else "author"
    if key not in poem_df.columns:
        raise ValueError("poem table needs author_id for merge")
    return poem_df.merge(meta, on=key, how="left")
