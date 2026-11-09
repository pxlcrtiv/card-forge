"""Offline, deterministic tests for card-forge. No network, no models."""

from __future__ import annotations

import json

from card_forge.cli import FIXTURES, facts_from, load_config
from card_forge.core import (
    ARCH_TASKS,
    Checklist,
    ModelFacts,
    detect_license,
    diff_configs,
    estimate_params,
    normalize_config,
    render_card,
    render_diff,
    score_checklist,
)

BERT = load_config(FIXTURES / "bert-tiny-config.json")
GPT2 = load_config(FIXTURES / "gpt2-tiny-config.json")
WHISPER = load_config(FIXTURES / "whisper-tiny-config.json")
CLIP = load_config(FIXTURES / "clip-tiny-config.json")
META = json.loads((FIXTURES / "demo-meta.json").read_text(encoding="utf-8"))


def bert_facts(**over) -> ModelFacts:
    return facts_from(BERT, over.get("name", META["name"]), over.get("license", META["license"]),
                      over.get("language", META["language"]), over.get("tags", list(META["tags"])))


# ---------------------------------------------------------------- task inference
def test_task_inference_mapping():
    if ARCH_TASKS["BertForSequenceClassification"][0] != "text-classification":
        raise AssertionError("BertForSequenceClassification task mismatch")
    if ARCH_TASKS["WhisperForConditionalGeneration"][0] != "automatic-speech-recognition":
        raise AssertionError("WhisperForConditionalGeneration task mismatch")
    if ARCH_TASKS["CLIPModel"][0] != "zero-shot-image-classification":
        raise AssertionError("CLIPModel task mismatch")
    if ARCH_TASKS["Qwen2ForCausalLM"][0] != "text-generation":
        raise AssertionError("Qwen2ForCausalLM task mismatch")


def test_unknown_architecture_has_no_task():
    facts = facts_from({"architectures": ["MyCustomModel"], "_model_name": "x"}, None, None, None, None)
    if facts.task_info() is not None:
        raise AssertionError("expected task_info() to be None for unknown architecture")


def test_missing_architectures_ok():
    facts = facts_from({"model_type": "bert", "_model_name": "x"}, None, None, None, None)
    if facts.architectures != []:
        raise AssertionError("expected empty architectures list")
    if facts.task_info() is not None:
        raise AssertionError("expected task_info() to be None when architectures missing")


# ---------------------------------------------------------------- params estimation
def test_params_bert_tiny_golden():
    # 4*V*H + 12*H^2*L = 4*30522*128 + 12*128*128*2
    if estimate_params(bert_facts()) != 4 * 30522 * 128 + 12 * 128 * 128 * 2:
        raise AssertionError("bert-tiny parameter count mismatch")


def test_params_gpt2_tiny_golden():
    if estimate_params(facts_from(GPT2, None, None, None, None)) != 4 * 50257 * 128 + 12 * 128 * 128 * 2:
        raise AssertionError("gpt2-tiny parameter count mismatch")


def test_params_whisper_tiny_golden():
    # 12*H^2*(enc+dec) + V*H + mel*H with H=384, enc=dec=4, V=51865, mel=80
    expected = 12 * 384 * 384 * 8 + 51865 * 384 + 80 * 384
    if estimate_params(facts_from(WHISPER, None, None, None, None)) != expected:
        raise AssertionError("whisper-tiny parameter count mismatch")


def test_params_clip_tiny_golden():
    vh = th = 64
    vl = tl = 2
    expected = 12 * vh * vh * vl + 12 * th * th * tl + 30522 * th
    if estimate_params(facts_from(CLIP, None, None, None, None)) != expected:
        raise AssertionError("clip-tiny parameter count mismatch")


def test_params_unknown_shape_returns_none():
    bare = facts_from({"architectures": ["BertForSequenceClassification"], "_model_name": "x"}, None, None, None, None)
    if estimate_params(bare) is not None:
        raise AssertionError("expected None for unknown shape params")


# ---------------------------------------------------------------- license
def test_license_detection_from_file(tmp_path):
    (tmp_path / "LICENSE").write_text("The MIT License (MIT) Copyright (c) 2026", encoding="utf-8")
    if detect_license(tmp_path, None) != "mit":
        raise AssertionError("expected MIT license detection")


def test_license_unknown_flag():
    if detect_license(None, None) != "unspecified":
        raise AssertionError("expected 'unspecified' license")
    if detect_license(None, "Apache-2.0") != "Apache-2.0":
        raise AssertionError("expected declared license to win")


# ---------------------------------------------------------------- checklist + card
def test_score_checklist_full_meta_is_band_a():
    checklist = score_checklist(bert_facts(), estimate_params(bert_facts()))
    if checklist.band != "A":
        raise AssertionError("expected band A")
    if checklist.missing != []:
        raise AssertionError("expected no missing items")


def test_score_checklist_bare_config_is_band_d():
    bare = facts_from(BERT, "x", None, None, None)
    checklist = score_checklist(bare, None)
    if checklist.band != "C":
        raise AssertionError("expected band C for bare config")
    if "declared license" not in checklist.missing:
        raise AssertionError("expected 'declared license' missing")
    if "parameter estimate" not in checklist.missing:
        raise AssertionError("expected 'parameter estimate' missing")


def test_card_render_contains_sections():
    checklist = score_checklist(bert_facts(), estimate_params(bert_facts()))
    card = render_card(bert_facts(), estimate_params(bert_facts()), checklist)
    for needle in ("# demo-bert-tiny", "MIT", "text-classification", "estimated", "Limitations", "Checklist"):
        if needle not in card:
            raise AssertionError(f"expected '{needle}' in rendered card")


def test_card_render_deterministic():
    checklist = score_checklist(bert_facts(), estimate_params(bert_facts()))
    a = render_card(bert_facts(), estimate_params(bert_facts()), checklist)
    b = render_card(bert_facts(), estimate_params(bert_facts()), checklist)
    if a != b:
        raise AssertionError("expected deterministic card output")


def test_card_render_uses_provided_checklist():
    checklist = Checklist(band="B", missing=["license"])
    card = render_card(bert_facts(), estimate_params(bert_facts()), checklist)
    if "**Checklist score:** B" not in card:
        raise AssertionError("expected band B in rendered card")
    if "- [ ] license" not in card:
        raise AssertionError("expected 'license' in rendered card")


# ---------------------------------------------------------------- diff
def test_normalize_config_flattens_nested():
    flat = normalize_config({"a": {"b": 1}, "c": 2})
    if flat != {"a.b": 1, "c": 2}:
        raise AssertionError("unexpected normalized config")


def test_diff_detects_changes():
    a = {"_model_name": "a", "hidden_size": 128, "labels": ["x"], "architectures": ["BertForSequenceClassification"]}
    b = {"_model_name": "b", "hidden_size": 256, "labels": ["x"], "num_labels": 2}
    d = diff_configs(a, b)
    if d.changed != {"hidden_size": (128, 256)}:
        raise AssertionError("unexpected changed fields")
    if d.added != ["num_labels"]:
        raise AssertionError("unexpected added fields")
    if d.removed != ["architectures"]:
        raise AssertionError("unexpected removed fields")


def test_diff_golden_between_bert_fixtures():
    gpt = dict(BERT, hidden_size=256, _model_name="gpt2-like")
    d = diff_configs(BERT, gpt)
    if d.changed_count != 1:
        raise AssertionError("expected changed_count == 1")
    if d.changed["hidden_size"] != (128, 256):
        raise AssertionError("unexpected hidden_size diff")


def test_diff_same_config_is_empty():
    d = diff_configs(BERT, dict(BERT))
    if d.changed_count != 0:
        raise AssertionError("expected no changes")
    if not d.summary_line().endswith("0 changed, 0 added, 0 removed"):
        raise AssertionError("unexpected summary line")


def test_render_diff_markdown():
    d = diff_configs({"a": 1, "_model_name": "one"}, {"a": 2, "b": 3, "_model_name": "two"})
    md = render_diff(d)
    if "`one` → `two`" not in md:
        raise AssertionError("expected model name transition in diff")
    if "`a`: 1 → 2" not in md:
        raise AssertionError("expected field change in diff")
    if "`b`" not in md:
        raise AssertionError("expected added field in diff")


# ---------------------------------------------------------------- CLI
def test_cli_demo_exit_zero(capsys):
    from card_forge.cli import main

    if main(["demo"]) != 0:
        raise AssertionError("expected exit code 0")
    out = capsys.readouterr().out
    if "demo-bert-tiny" not in out:
        raise AssertionError("expected 'demo-bert-tiny' in output")
    if "**Checklist score:** A" not in out:
        raise AssertionError("expected band A in output")


def test_cli_generate_fixture(capsys):
    from card_forge.cli import main

    if main(["generate", str(FIXTURES / "whisper-tiny-config.json")]) != 0:
        raise AssertionError("expected exit code 0")
    out = capsys.readouterr().out
    if "WhisperForConditionalGeneration" not in out:
        raise AssertionError("expected architecture in output")
    if "automatic-speech-recognition" not in out:
        raise AssertionError("expected task in output")


def test_cli_generate_json(capsys):
    from card_forge.cli import main

    if main(["generate", str(FIXTURES / "bert-tiny-config.json"), "--format", "json"]) != 0:
        raise AssertionError("expected exit code 0")
    payload = json.loads(capsys.readouterr().out)
    if payload["task"] != "text-classification":
        raise AssertionError("unexpected task")
    if payload["params_estimated"] != 4 * 30522 * 128 + 12 * 128 * 128 * 2:
        raise AssertionError("unexpected params_estimated")


def test_cli_diff_json(capsys):
    from card_forge.cli import main

    gpt = str(FIXTURES / "gpt2-tiny-config.json")
    if main(["diff", str(FIXTURES / "bert-tiny-config.json"), gpt, "--format", "json"]) != 0:
        raise AssertionError("expected exit code 0")
    payload = json.loads(capsys.readouterr().out)
    if payload["a"] != "demo-bert-tiny":
        raise AssertionError("unexpected model name in diff payload")
    if len(payload["changed"]) == 0:
        raise AssertionError("expected non-empty changed list")


def test_cli_tasks_nonempty(capsys):
    from card_forge.cli import main

    if main(["tasks"]) != 0:
        raise AssertionError("expected exit code 0")
    if "text-generation" not in capsys.readouterr().out:
        raise AssertionError("expected text-generation in tasks output")


def test_cli_generate_missing_file(capsys):
    from card_forge.cli import main

    if main(["generate", "/nonexistent/config.json"]) != 1:
        raise AssertionError("expected exit code 1 for missing file")
    if "not found" not in capsys.readouterr().err:
        raise AssertionError("expected 'not found' in stderr")


def test_cli_hf_without_dependency(monkeypatch, capsys):
    from card_forge import cli

    def boom(repo_id):
        raise RuntimeError("live Hub fetch needs the optional dependency")

    monkeypatch.setattr(cli, "fetch_hf_config", boom)
    if cli.main(["generate", "--hf", "some/repo"]) != 2:
        raise AssertionError("expected exit code 2")
    if "optional dependency" not in capsys.readouterr().err:
        raise AssertionError("expected 'optional dependency' in stderr")


# ---------------------------------------------------------------- CLI handler unit tests (post-dispatcher)
def test_cmd_tasks_nonempty(capsys):
    from card_forge.cli import cmd_tasks

    if cmd_tasks() != 0:
        raise AssertionError("expected exit code 0")
    if "text-generation" not in capsys.readouterr().out:
        raise AssertionError("expected text-generation in tasks output")


def test_cmd_demo_exit_zero(capsys):
    from card_forge.cli import cmd_demo

    if cmd_demo() != 0:
        raise AssertionError("expected exit code 0")
    out = capsys.readouterr().out
    if "demo-bert-tiny" not in out:
        raise AssertionError("expected 'demo-bert-tiny' in output")
    if "**Checklist score:** A" not in out:
        raise AssertionError("expected band A in output")


def test_cmd_generate_fixture(capsys):
    from card_forge.cli import build_parser, cmd_generate

    args = build_parser().parse_args(["generate", str(FIXTURES / "whisper-tiny-config.json")])
    if cmd_generate(args) != 0:
        raise AssertionError("expected exit code 0")
    out = capsys.readouterr().out
    if "WhisperForConditionalGeneration" not in out:
        raise AssertionError("expected architecture in output")
    if "automatic-speech-recognition" not in out:
        raise AssertionError("expected task in output")


def test_cmd_generate_json(capsys):
    from card_forge.cli import build_parser, cmd_generate

    args = build_parser().parse_args([
        "generate", str(FIXTURES / "bert-tiny-config.json"), "--format", "json"
    ])
    if cmd_generate(args) != 0:
        raise AssertionError("expected exit code 0")
    payload = json.loads(capsys.readouterr().out)
    if payload["task"] != "text-classification":
        raise AssertionError("unexpected task")
    if payload["params_estimated"] != 4 * 30522 * 128 + 12 * 128 * 128 * 2:
        raise AssertionError("unexpected params_estimated")


def test_cmd_diff_json(capsys):
    from card_forge.cli import build_parser, cmd_diff

    gpt = str(FIXTURES / "gpt2-tiny-config.json")
    args = build_parser().parse_args(["diff", str(FIXTURES / "bert-tiny-config.json"), gpt, "--format", "json"])
    if cmd_diff(args) != 0:
        raise AssertionError("expected exit code 0")
    payload = json.loads(capsys.readouterr().out)
    if payload["a"] != "demo-bert-tiny":
        raise AssertionError("unexpected model name in diff payload")
    if len(payload["changed"]) == 0:
        raise AssertionError("expected non-empty changed list")


def test_cmd_generate_missing_file(capsys):
    from card_forge.cli import build_parser, cmd_generate

    args = build_parser().parse_args(["generate", "/nonexistent/config.json"])
    if cmd_generate(args) != 1:
        raise AssertionError("expected exit code 1 for missing file")
    if "not found" not in capsys.readouterr().err:
        raise AssertionError("expected 'not found' in stderr")


def test_cmd_hf_without_dependency(monkeypatch, capsys):
    import card_forge.cli as cli_mod
    from card_forge.cli import build_parser, cmd_generate

    def boom(repo_id):
        raise RuntimeError("live Hub fetch needs the optional dependency")

    monkeypatch.setattr(cli_mod, "fetch_hf_config", boom)
    args = build_parser().parse_args(["generate", "--hf", "some/repo"])
    if cmd_generate(args) != 2:
        raise AssertionError("expected exit code 2")
    if "optional dependency" not in capsys.readouterr().err:
        raise AssertionError("expected 'optional dependency' in stderr")