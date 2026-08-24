# Contributing

Thanks for helping make card-forge better. This is a focused, deterministic
model-card generator: **offline-testable, zero-runtime-dependencies, honest
about what it infers**. Please keep those properties.

## Ground rules

- **No runtime dependencies.** Card generation and diffing are pure
  Python stdlib. Live Hub fetching (`card-forge[live]`) is an optional
  extra, lazily required, never in the default path.
- **Deterministic output.** Same config + same metadata → same card, same
  score, same diff. No timestamps, no randomness.
- **Honest inference.** Everything derived from config geometry is labeled
  as an estimate; unknown facts are marked unknown, never guessed.
- **Golden tests for every behavior change.** New architectures, param
  formulas, or render output must update the goldens in `tests/`
  deliberately.
- **Tests stay offline.** No network, no model downloads, ever.

## Daily Green

The repo commits one dated entry per day via `scripts/daily_update.py`
(pool: `scripts/tips_pool.json`). Add model-card tips to the pool; never
edit `docs/daily-tips.md` by hand.

## PR process

1. Fork, branch, change, test: `python -m pytest tests/ -q` (all green).
2. `ruff check card_forge tests scripts` clean.
3. CLI smoke: `card-forge demo | head`.
4. Reference the golden numbers you changed (and why) in the PR body.

## Style

- Type hints on all public functions; `py3.10+`.
- New architecture mappings go in `ARCH_TASKS` with task, metrics, usage
  snippet, and a specific limitation — four fields, no exceptions.