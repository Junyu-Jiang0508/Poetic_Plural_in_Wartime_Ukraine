# Poetic Plural in Wartime Ukraine

Within-author analysis of first-person pronoun use in Ukrainian war poetry (2014–2025).

This repository reproduces the paper's statistical models and figures from **anonymized**
poem-level count data. It ships no poet names, no poem texts, and no AI annotation prompts.

## Data

| File | Description |
|------|-------------|
| `data/pronoun_cell_counts.csv` | Per-poem pronoun cell counts with opaque `author_id` |
| `data/author_meta.csv` | `author_id`, `in_ukraine_2022`, `language` only |

Regenerate locally (requires private covariates — **do not commit** the crosswalk):

```bash
python tools/anonymize_export.py \
  --counts /path/to/roster_poem_cell_counts.csv \
  --covariates /path/to/author_covariates.csv \
  --outdir data
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download uk_core_news_sm
```

## Modeling scripts

Primary model (Fig 1):

```bash
PYTHONPATH=src python src/modeling/glmm_within_author.py
```

See `docs/PREREGISTRATION.md` and `docs/core_contrasts_prespec.md` for prespecified contrasts.

## Privacy

The legacy archive repo must remain **private**. This clean repo does not neutralize a still-public
copy of named covariates or attributed poem texts.
