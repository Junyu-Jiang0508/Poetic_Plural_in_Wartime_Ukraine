"""Repository layout and canonical paths for the anonymized public replication repo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "repository_root",
    "repository_root_for_script",
    "prepare_analysis_environment",
    "canonical_poem_cell_counts_csv",
    "canonical_author_meta_csv",
    "canonical_roster_csv",
    "canonical_collocations_csv",
    "canonical_pronoun_annotation_csv",
    "CANONICAL_POEM_CELL_COUNTS_RELPATH",
    "CANONICAL_AUTHOR_META_RELPATH",
    "CANONICAL_ROSTER_RELPATH",
    "CANONICAL_COLLOCATIONS_RELPATH",
]

CANONICAL_POEM_CELL_COUNTS_RELPATH = ("data", "pronoun_cell_counts.csv")
CANONICAL_AUTHOR_META_RELPATH = ("data", "author_meta.csv")
CANONICAL_ROSTER_RELPATH = ("data", "roster_v1_frozen.csv")
CANONICAL_COLLOCATIONS_RELPATH = ("data", "collocations_pronoun_head.csv")


def repository_root_for_script(script_file: str | Path) -> Path:
    p = Path(script_file).resolve()
    if p.parent.name in {"utils", "annotation", "modeling"}:
        return p.parent.parent.parent
    if p.parent.name == "tools":
        return p.parent.parent
    return p.parent.parent


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def prepare_analysis_environment(
    script_file: str | Path,
    *,
    matplotlib_backend: str | None = "Agg",
) -> Path:
    root = repository_root_for_script(script_file)
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    os.chdir(root)
    if matplotlib_backend:
        import matplotlib
        matplotlib.use(matplotlib_backend)
    return root


def canonical_poem_cell_counts_csv(root: Path | None = None) -> Path:
    env = os.environ.get("POEM_CELL_COUNTS_CSV")
    if env:
        return Path(env)
    r = root if root is not None else repository_root()
    return r.joinpath(*CANONICAL_POEM_CELL_COUNTS_RELPATH)


def canonical_author_meta_csv(root: Path | None = None) -> Path:
    env = os.environ.get("AUTHOR_META_CSV")
    if env:
        return Path(env)
    r = root if root is not None else repository_root()
    return r.joinpath(*CANONICAL_AUTHOR_META_RELPATH)


def canonical_roster_csv(root: Path | None = None) -> Path:
    env = os.environ.get("ROSTER_CSV")
    if env:
        return Path(env)
    r = root if root is not None else repository_root()
    return r.joinpath(*CANONICAL_ROSTER_RELPATH)


def canonical_collocations_csv(root: Path | None = None) -> Path:
    env = os.environ.get("COLLOCATIONS_CSV")
    if env:
        return Path(env)
    r = root if root is not None else repository_root()
    return r.joinpath(*CANONICAL_COLLOCATIONS_RELPATH)


def canonical_pronoun_annotation_csv(root: Path | None = None) -> Path:
    """Legacy alias: public repo ships poem-level counts, not sentence-level annotation."""
    return canonical_poem_cell_counts_csv(root)
