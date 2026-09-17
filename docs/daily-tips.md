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


## 2026-09-05 — Model-card tip of the day: Aliases die; ids do not

Linking cards by repo name breaks on renames. Store model ids, config hashes, and revision pins in the card so the artifact stays traceable after the rename.


## 2026-09-06 — Model-card tip of the day: A model card is a contract

The card tells a downstream user what they may assume: license, task, data, limits. Card-less models get misused in production, then the misuse is blamed on the model.

> `card-forge generate ./config.json`


## 2026-09-07 — Model-card tip of the day: License honesty beats license hope

An undeclared license is a legal wall: nobody can ship your model anywhere. Detect from LICENSE or declare explicitly; 'unspecified' is a red flag, not a neutral state.

> `card-forge generate ./config.json --license MIT`


## 2026-09-08 — Model-card tip of the day: Parameters are context, not bragging

A parameter count without a task says nothing. Report params next to task and metrics so readers can judge fit — a 16M classifier and a 1B chat model are different products.


## 2026-09-09 — Model-card tip of the day: Infer tasks, then verify

An architecture implies a task family, not the deployment task. A BertForSequenceClassification could be spam, sentiment, or toxicity — generate the skeleton, then state the real task in prose.

> `card-forge tasks`


## 2026-09-10 — Model-card tip of the day: Metrics belong to the target domain

SQuAD F1 does not transfer to legal QA. Pick the metric for the actual deployment distribution, and say which dataset it was measured on.


## 2026-09-11 — Model-card tip of the day: Limitations are features

A card that states 'expects aligned audio; WER collapses on music' saves integrations. Generic limitation boilerplate is ignored; specific ones get quoted in design docs.


## 2026-09-12 — Model-card tip of the day: Benchmark numbers age

A card with numbers from last year is a historical artifact. Date every metric and re-run before major releases; an honest 'not re-evaluated in 6 months' beats stale precision.


## 2026-09-13 — Model-card tip of the day: Config diffing catches silent swaps

A shadow-updated config (hidden_size changed, version not bumped) silently breaks downstream assumptions. Diff configs in review before merging model updates.

> `card-forge diff old/config.json new/config.json`


## 2026-09-14 — Model-card tip of the day: Checklists automate quality

A 0-100 documentation score turns 'please improve the card' into a measurable gate. Enforce a minimum band in CI and watch cards stop rotting.

> `card-forge generate ./config.json --format json`


## 2026-09-15 — Model-card tip of the day: The card is part of the release

Ship config, weights, and card as one artifact. A model without its card in the release notes is half-released; rollback decisions need the card to know what changed.


## 2026-09-16 — Model-card tip of the day: Language fields matter

'en' is a claim about the training distribution. Multi-lingual fine-tunes must say which languages and in what proportion — evaluation leaks otherwise.

> `card-forge generate ./config.json --language en`


## 2026-09-17 — Model-card tip of the day: Tags are the discovery layer

The Hub search is tag-driven. Two or three honest tags (task, domain, format) beat a dozen marketing ones; tags you cannot defend in a review get removed anyway.

