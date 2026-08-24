# Changelog

All notable changes to card-forge are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] — 2026-08-24

### Added
- Initial release: `card-forge` CLI that generates complete Hugging Face
  model cards from config facts — architecture → task inference (11 known
  mappings), order-of-magnitude parameter estimation from config geometry
  (BERT/GPT-2/Whisper/CLIP formulas), LICENSE-file sniffing with declared
  overrides, language/tags metadata, actionable 0–100 checklist score with
  A–D bands, and honest 'unknown/estimated' labels throughout.
- `generate` (config path, model dir, or `--hf REPO_ID` live fetch with
  graceful no-dependency error), `diff` (flattened-key config diffing with
  added/removed/changed sections, metadata keys excluded), `demo` (bundled
  fixture card), `tasks` (mapping reference).
- Four bundled fixture configs (BERT/GPT-2/Whisper/CLIP shapes) with golden
  param estimates; markdown/JSON output; 26-offline-test suite; Daily
  Green automation (22-model-card-tip pool); CI + daily workflows.