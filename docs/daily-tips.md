# card-forge tips of the day

> Maintained by `scripts/daily_update.py` (Daily Green automation) — one
> dated, non-empty model-card/MLOps tip per day, rotated from the pool
> in `scripts/tips_pool.json`. Pause by creating a `.daily-pause` file
> in the repo root, or unload the scheduler job (see README,
> Daily Green).


## 2026-08-24 — Model-card tip of the day: The card is part of the release

Ship config, weights, and card as one artifact. A model without its card in the release notes is half-released; rollback decisions need the card to know what changed.


## 2026-08-25 — Model-card tip of the day: Language fields matter

'en' is a claim about the training distribution. Multi-lingual fine-tunes must say which languages and in what proportion — evaluation leaks otherwise.

> `card-forge generate ./config.json --language en`


## 2026-08-26 — Model-card tip of the day: Tags are the discovery layer

The Hub search is tag-driven. Two or three honest tags (task, domain, format) beat a dozen marketing ones; tags you cannot defend in a review get removed anyway.


## 2026-08-27 — Model-card tip of the day: Estimates deserve the word 'estimated'

A param count computed from config geometry is an approximation (tied embeddings, head sizes, MoE experts change it). Label it or someone will quote it as exact.


## 2026-08-28 — Model-card tip of the day: For the unknown: say nothing, not anything

Training data, bias evals, and fine-tune datasets are often unknown. The card should mark them unknown — a confident-looking empty section reads as a decision, not an omission.

