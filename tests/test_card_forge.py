"""Offline, deterministic tests for card-forge. No network, no models."""

from __future__ import annotations

import json

from card_forge.cli import FIXTURES, facts_from, load_config
from card_forge.core import (
    ARCH_TASKS,
    ModelFacts,
    checklist_score,
    detect_license,
    diff_configs,
    estimate_params,
    normalize_config,
    render_card,
    render_diff,
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
    assert ARCH_TASKS["BertForSequenceClassification"][0] == "text-classification"
    assert ARCH_TASKS["WhisperForConditionalGeneration"][0] == "automatic-speech-recognition"
    assert ARCH_TASKS["CLIPModel"][0] == "zero-shot-image-classification"
    assert ARCH_TASKS["Qwen2ForCausalLM"][0] == "text-generation"


def test_unknown_architecture_has_no_task():
    facts = facts_from({"architectures": ["MyCustomModel"], "_model_name": "x"}, None, None, None, None)
    assert facts.task_info() is None


def test_missing_architectures_ok():
    facts = facts_from({"model_type": "bert", "_model_name": "x"}, None, None, None, None)
    assert facts.architectures == []
    assert facts.task_info() is None


# ---------------------------------------------------------------- params estimation
def test_params_bert_tiny_golden():
    # 4*V*H + 12*H^2*L = 4*30522*128 + 12*128*128*2
    assert estimate_params(bert_facts()) == 4 * 30522 * 128 + 12 * 128 * 128 * 2


def test_params_gpt2_tiny_golden():
    assert estimate_params(facts_from(GPT2, None, None, None, None)) == 4 * 50257 * 128 + 12 * 128 * 128 * 2


def test_params_whisper_tiny_golden():
    # 12*H^2*(enc+dec) + V*H + mel*H with H=384, enc=dec=4, V=51865, mel=80
    assert estimate_params(facts_from(WHISPER, None, None, None, None)) == (
        12 * 384 * 384 * 8 + 51865 * 384 + 80 * 384
    )


def test_params_clip_tiny_golden():
    vh = th = 64
    vl = tl = 2
    expected = 12 * vh * vh * vl + 12 * th * th * tl + 30522 * th
    assert estimate_params(facts_from(CLIP, None, None, None, None)) == expected


def test_params_unknown_shape_returns_none():
    bare = facts_from({"architectures": ["BertForSequenceClassification"], "_model_name": "x"}, None, None, None, None)
    assert estimate_params(bare) is None


# ---------------------------------------------------------------- license
def test_license_detection_from_file(tmp_path):
    (tmp_path / "LICENSE").write_text("The MIT License (MIT) Copyright (c) 2026", encoding="utf-8")
    assert detect_license(tmp_path, None) == "mit"


def test_license_unknown_flag():
    assert detect_license(None, None) == "unspecified"
    assert detect_license(None, "Apache-2.0") == "Apache-2.0"  # declared wins


# ---------------------------------------------------------------- checklist + card
def test_checklist_score_full_meta_is_band_a():
    band, missing = checklist_score(bert_facts(), estimate_params(bert_facts()))
    assert band == "A"
    assert missing == []


def test_checklist_score_bare_config_is_band_d():
    bare = facts_from(BERT, "x", None, None, None)
    band, missing = checklist_score(bare, None)
    assert band == "C"  # arch still yields task inference (15 pts) over a total of 55
    assert "declared license" in missing and "parameter estimate" in missing


def test_card_render_contains_sections():
    card = render_card(bert_facts(), estimate_params(bert_facts()))
    for needle in ("# demo-bert-tiny", "MIT", "text-classification", "estimated", "Limitations", "Checklist"):
        assert needle in card


def test_card_render_deterministic():
    a = render_card(bert_facts(), estimate_params(bert_facts()))
    b = render_card(bert_facts(), estimate_params(bert_facts()))
    assert a == b


# ---------------------------------------------------------------- diff
def test_normalize_config_flattens_nested():
    flat = normalize_config({"a": {"b": 1}, "c": 2})
    assert flat == {"a.b": 1, "c": 2}


def test_diff_detects_changes():
    a = {"_model_name": "a", "hidden_size": 128, "labels": ["x"], "architectures": ["BertForSequenceClassification"]}
    b = {"_model_name": "b", "hidden_size": 256, "labels": ["x"], "num_labels": 2}
    d = diff_configs(a, b)
    assert d.changed == {"hidden_size": (128, 256)}
    assert d.added == ["num_labels"]
    assert d.removed == ["architectures"]


def test_diff_golden_between_bert_fixtures():
    gpt = dict(BERT, hidden_size=256, _model_name="gpt2-like")
    d = diff_configs(BERT, gpt)
    assert d.changed_count == 1
    assert d.changed["hidden_size"] == (128, 256)


def test_diff_same_config_is_empty():
    d = diff_configs(BERT, dict(BERT))
    assert d.changed_count == 0
    assert d.summary_line().endswith("0 changed, 0 added, 0 removed")


def test_render_diff_markdown():
    d = diff_configs({"a": 1, "_model_name": "one"}, {"a": 2, "b": 3, "_model_name": "two"})
    md = render_diff(d)
    assert "`one` → `two`" in md and "`a`: 1 → 2" in md and "`b`" in md


# ---------------------------------------------------------------- CLI
def test_cli_demo_exit_zero(capsys):
    from card_forge.cli import main

    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "demo-bert-tiny" in out and "**Checklist score:** A" in out


def test_cli_generate_fixture(capsys):
    from card_forge.cli import main

    assert main(["generate", str(FIXTURES / "whisper-tiny-config.json")]) == 0
    out = capsys.readouterr().out
    assert "WhisperForConditionalGeneration" in out and "automatic-speech-recognition" in out


def test_cli_generate_json(capsys):
    from card_forge.cli import main

    assert main(["generate", str(FIXTURES / "bert-tiny-config.json"), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task"] == "text-classification"
    assert payload["params_estimated"] == 4 * 30522 * 128 + 12 * 128 * 128 * 2


def test_cli_diff_json(capsys):
    from card_forge.cli import main

    gpt = str(FIXTURES / "gpt2-tiny-config.json")
    assert main(["diff", str(FIXTURES / "bert-tiny-config.json"), gpt, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["a"] == "demo-bert-tiny"
    assert len(payload["changed"]) > 0


def test_cli_tasks_nonempty(capsys):
    from card_forge.cli import main

    assert main(["tasks"]) == 0
    assert "text-generation" in capsys.readouterr().out


def test_cli_generate_missing_file(capsys):
    from card_forge.cli import main

    assert main(["generate", "/nonexistent/config.json"]) == 1
    assert "not found" in capsys.readouterr().err


def test_cli_hf_without_dependency(monkeypatch, capsys):
    from card_forge import cli

    def boom(repo_id):
        raise RuntimeError("live Hub fetch needs the optional dependency")

    monkeypatch.setattr(cli, "fetch_hf_config", boom)
    assert cli.main(["generate", "--hf", "some/repo"]) == 2
    assert "optional dependency" in capsys.readouterr().err