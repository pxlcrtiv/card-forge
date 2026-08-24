# card-forge

[![CI](https://img.shields.io/github/actions/workflow/status/pxlcrtiv/card-forge/ci.yml?branch=main&label=CI)](https://github.com/pxlcrtiv/card-forge/actions)
[![License](https://img.shields.io/github/license/pxlcrtiv/card-forge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/pxlcrtiv/card-forge)](https://github.com/pxlcrtiv/card-forge/stargazers)
[![Forks](https://img.shields.io/github/forks/pxlcrtiv/card-forge)](https://github.com/pxlcrtiv/card-forge/forks)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000)](https://github.com/astral-sh/ruff)

**Forge complete Hugging Face model cards from config facts — and diff
configs between revisions.** Task inference, license detection, honest
parameter estimates, an actionable documentation score, and a config
`diff` that catches silent swaps. Pure stdlib, deterministic, offline
fixtures or live Hub. **Zero runtime dependencies, zero keys.**

## Problem

- Model cards are the most ignored artifact in ML: most Hub repos have
  none, an empty stub, or a license-less header that nobody can legally
  ship downstream.
- Writing a card by hand means re-deriving task, params, and usage from a
  config every time — then the config changes and the card is stale.
- Config files silently mutate (hidden_size bumps, arch swaps, vocab
  changes) without version bumps, breaking downstream assumptions.

## Solution

`card-forge` turns a `config.json` (or a live Hub repo id) into a complete,
honest card:

| What it does | How |
| --- | --- |
| Task inference | 11 known `architecture → task` mappings (text-classification, QA, ASR, zero-shot image, text-generation, …) with recommended metrics + usage snippet |
| Parameter estimate | order-of-magnitude from config geometry (BERT/GPT-2/Whisper/CLIP formulas), labeled `(estimated)` or `not estimable` |
| License | declared field, else LICENSE-file sniffing (10 known licenses), else explicit `unspecified` — never a silent blank |
| Checklist score | 0–100 documentation completeness with an actionable missing-items list, A–D bands |
| Config diff | flattened-key diff of two configs (added/removed/changed), metadata keys excluded |

Everything is deterministic: same config bytes in → same card bytes out.
Unknown facts are marked unknown, never guessed.

## Quickstart

```bash
git clone https://github.com/pxlcrtiv/card-forge
cd card-forge
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

```bash
card-forge demo    # bundled fixture card
card-forge generate ./path/to/config.json --license MIT --language en
card-forge generate --hf sshleifer/tiny-gpt2     # live Hub (extra: pip install .[live])
card-forge diff old/config.json new/config.json
```

## Demo (live transcript, 2026-08-24)

The bundled demo fixture (BERT-small classifier, MIT, en):

```text
$ card-forge demo
# demo-bert-tiny

- **License:** MIT
- **Model type:** bert
- **Architectures:** BertForSequenceClassification
- **Language:** en
- **Parameters:** 16,020,480 (estimated)
- **Checklist score:** A

## Intended use

- Task: `text-classification`
- Metrics: accuracy (per-class F1 for imbalanced sets)

```python
classifier = pipeline("text-classification", model="demo-bert-tiny")
```

## Limitations and risks

- Scores depend heavily on the training distribution; verify on your own label set before rollout.

- This card was generated from config facts; benchmark numbers,
  training data details, and bias evaluations must be filled in by
  the model author.
```

A real model fetched live from the Hub, keyless:

```text
$ pip install "card-forge[live]"
$ card-forge generate --hf sshleifer/tiny-gpt2
# tiny-gpt2

- **License:** unspecified
- **Model type:** gpt2
- **Architectures:** GPT2LMHeadModel
- **Language:** unspecified
- **Parameters:** 402,152 (estimated)
- **Checklist score:** B

## Intended use

- Task: `text-generation`
- Metrics: perplexity; human preference for open-ended use
```

Note what the card does *not* do: it does not invent a license or a
language for a repo that declares neither. `unspecified` is a flagged
action item, not a blank.

And the config diff:

```text
$ card-forge diff card_forge/data/fixtures/gpt2-tiny-config.json card_forge/data/fixtures/whisper-tiny-config.json
# Config diff

- `demo-gpt2-tiny` → `demo-whisper-tiny`
- 13 differences

## Added keys
- `d_model`
- `decoder_layers`
- `encoder_layers`
- `max_source_positions`
- `max_target_positions`
- `num_mel_bins`
...
```

## Commands

```bash
# generate a card (config path, model directory, or live Hub id)
card-forge generate [config.json | dir/ | --hf repo_id]
card-forge generate ./config.json --name my-model --license Apache-2.0 --language en --tag llm --tag decoder-only
card-forge generate ./config.json --format json        # machine-readable facts

# compare two revisions
card-forge diff before/config.json after/config.json
card-forge diff --a-hf org/model --b-hf org/model  # live comparison

# reference + demo
card-forge tasks
card-forge demo
```

## How it works

1. **Load** — a config JSON (or `config.json` inside a directory, or a
   live Hub fetch via the optional `huggingface-hub` extra — graceful
   error if the extra is missing).
2. **Infer** — `architecture → task` from `ARCH_TASKS`; parameters from
   config geometry using documented transformer-count formulas
   (`12·H²·L` + embeddings, Whisper enc/dec split, CLIP dual-encoder);
   license from declaration → `LICENSE` file → `unspecified`.
3. **Score** — checklist points for name, license, task, params,
   architecture, language, tags, and `model_type`; band A–D; missing
   items rendered as a checkbox list for the author.
4. **Diff** — configs are flattened to dotted keys (metadata `_`-keys
   excluded) and compared; results render as a stable markdown table or
   JSON.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -q        # 26 offline, deterministic tests (0.05s)
ruff check card_forge tests scripts
```

Goldens cover task inference, every parameter formula, license detection,
checklist bands, diff semantics, and CLI exit codes.

## Related portfolio repos

Built alongside my AI/ML × blockchain tooling: [**hf-hub-lint**](
https://github.com/pxlcrtiv/hf-hub-lint) (scores Hub repos' hygiene —
card-forge writes the cards that lint checks), [**pocket-eval**](
https://github.com/pxlcrtiv/pocket-eval) (keyless CPU LLM eval harness)
and [**embed-playground**](https://github.com/pxlcrtiv/embed-playground)
(lexical vs dense search). See the full portfolio on my
[profile](https://github.com/pxlcrtiv).

## Daily Green automation

This repo participates in the portfolio-wide daily-commit automation
(launchd on macOS 12:07 + 18:07 local, GitHub Actions
[`daily.yml`](.github/workflows/daily.yml) 12:00 UTC as cloud fallback).
Every day `scripts/daily_update.py` appends one curated model-card tip from
`scripts/tips_pool.json` (22 entries) to `docs/daily-tips.md` and pushes a
dated, non-empty commit — idempotent, backfills missed days (max 14), and
never duplicates.

- Customize content: edit `scripts/tips_pool.json`.
- Pause this repo: `touch .daily-pause`.
- Pause globally: `launchctl bootout gui/$(id -u)/com.pxlcrtiv.daily-green`.

## License

MIT — see [LICENSE](LICENSE).