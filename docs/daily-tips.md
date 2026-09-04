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


## 2026-08-29 — Model-card tip of the day: Diff before you double-check

Two configs that look identical in a PR can differ in one dim. Diff output gives reviewers a precise changed-keys list instead of eyeballing thousands of JSON lines.

> `card-forge diff a/config.json b/config.json --format json`


## 2026-08-30 — Model-card tip of the day: Model cards rot like code

Treat the card as living documentation: update it when the config changes, link the card commit to the weights commit, and review it in the same PR.


## 2026-08-31 — Model-card tip of the day: Usage snippets are trust builders

A copy-pasteable pipeline snippet converts a spec into a tool. People evaluate snippets first; a snippet that runs on the first try is the strongest quality signal.


## 2026-09-01 — Model-card tip of the day: One card, one contract

Don't merge two tasks into one card ('text-classification + QA') — the license, metrics, and limits differ. Split cards per task even if the weights are shared.


## 2026-09-02 — Model-card tip of the day: Documentation debt is model debt

Every undocumented model you publish is a support ticket you will answer later, forever. Card generation at release time is cheaper than triage at adoption time.


## 2026-09-03 — Model-card tip of the day: Deterministic generation, human judgment

An auto-generated card is a first draft that never lies. Keep the generation deterministic, then let a human edit the parts only humans know: data provenance and failure modes.

> `card-forge demo`


## 2026-09-04 — Model-card tip of the day: Reproduce, then report

If a metric cannot be reproduced from the card (model id, config, eval script), it is marketing. Make 'reproduce this card's numbers' a CI job, not a promise.

