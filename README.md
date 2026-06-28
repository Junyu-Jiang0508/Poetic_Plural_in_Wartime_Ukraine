# Poetic Plural in Wartime Ukraine

Within-author analysis of first-person pronoun use in Ukrainian war poetry (2014–2025).

This repository ships **anonymized poem-level count tables** and the **modeling code**
needed to reproduce the paper's inferential figures and statistics. No poet names, no
poem texts, and no AI annotation prompts are included.

## Data (public)

| File | Rows (current export) | Description |
|------|----------------------:|-------------|
| `data/pronoun_cell_counts.csv` | 1,527 poems × **33 authors** | Paper-modeled roster; Q1 pipeline exclusions applied |
| `data/author_meta.csv` | 33 | `author_id`, `in_ukraine_2022`, `language` |
| `data/roster_v1_frozen.csv` | 33 | Anonymized roster flags (`author_id`, `included`) |
| `data/collocations_pronoun_head.csv` | 5,252 | Aggregated pronoun→head-lemma counts by period (no authors) |

**Note on N.** The manuscript's *inferential corpus* is 1,601 poems by 105 authors (after
translation/repost/Crimean Tatar exclusion). Confirmatory within-author models use the
**33-author modeled roster** (poets with poems on both sides of 2022); that subset is
what `pronoun_cell_counts.csv` contains. The table ships first/second-person cells only
(`1sg`, `1pl`, `2sg`, `2pl_*`), not third-person columns.

Regenerate locally (requires private covariates — **do not commit** `name_crosswalk.csv`):

```bash
python tools/anonymize_export.py \
  --counts /path/to/q1_poem_unit_cell_counts_12.csv \
  --covariates /path/to/author_covariates.csv \
  --roster /path/to/author_covariates_paper_roster_n33.csv \
  --outdir data

python tools/export_collocations_public.py \
  --input /path/to/collocations_by_cell_period.csv \
  --output data/collocations_pronoun_head.csv
```

Run counts + meta + crosswalk in **one** `anonymize_export.py` invocation so `author_id`
codes stay aligned.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download uk_core_news_sm
```

## Reproduce from shipped CSVs

Per-cell GLM (RQ2 secondary / absolute salience):

```bash
PYTHONPATH=src python src/modeling/per_cell_glm.py
```

Hierarchical GLMM (RQ2 primary):

```bash
PYTHONPATH=src python src/modeling/glmm_within_author.py
```

Collocation analysis (including the «мусити» finding):

```bash
PYTHONPATH=src python src/modeling/collocations.py
```

Narrative figures:

```bash
PYTHONPATH=src python src/modeling/figures.py
```

All four scripts default to `data/pronoun_cell_counts.csv` or `data/collocations_pronoun_head.csv`.

## Privacy

- `name_crosswalk.csv` is gitignored and must never be pushed.
- The legacy archive repo must remain **private**; this clean repo does not neutralize a
  still-public copy of named covariates or attributed poem texts.

See `docs/PREREGISTRATION.md` and `docs/core_contrasts_prespec.md` for prespecified contrasts.
