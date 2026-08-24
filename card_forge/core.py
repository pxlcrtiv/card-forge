"""card-forge core: task inference, params estimation, card rendering, diffing.

Everything here is pure stdlib and deterministic: same config bytes in,
same card bytes out.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# arch -> (task, recommended metrics, usage snippet, limitation text)
ARCH_TASKS: dict[str, tuple[str, str, str, str]] = {
    "BertForSequenceClassification": (
        "text-classification",
        "accuracy (per-class F1 for imbalanced sets)",
        'classifier = pipeline("text-classification", model="<model-id>")',
        "Scores depend heavily on the training distribution; verify on your own label set before rollout.",
    ),
    "BertForTokenClassification": (
        "token-classification",
        "span-level precision / recall / F1",
        'ner = pipeline("token-classification", model="<model-id>")',
        "Entity boundary errors are common; evaluate on your annotation scheme, not a borrowed one.",
    ),
    "BertForQuestionAnswering": (
        "question-answering",
        "exact match + (SQuAD-style) F1",
        'qa = pipeline("question-answering", model="<model-id>")',
        "Extractive readers cannot answer questions whose evidence is not literally present in the context.",
    ),
    "GPT2LMHeadModel": (
        "text-generation",
        "perplexity; human preference for open-ended use",
        'gen = pipeline("text-generation", model="<model-id>")',
        "Generated text can be plausible but wrong; add a verification layer for any factual use.",
    ),
    "T5ForConditionalGeneration": (
        "text2text-generation",
        "task-appropriate (ROUGE for summarization, sacreBLEU for MT)",
        't5 = pipeline("text2text-generation", model="<model-id>")',
        "T5-style models are strong at format transfer; measure the target task, not just fluency.",
    ),
    "WhisperForConditionalGeneration": (
        "automatic-speech-recognition",
        "WER on the target accent/domain, not just LibriSpeech",
        'asr = pipeline("automatic-speech-recognition", model="<model-id>")',
        "WER collapses on out-of-domain audio: music, accents, and jargon need their own eval set.",
    ),
    "WhisperForAudioClassification": (
        "audio-classification",
        "accuracy + per-class F1",
        'clf = pipeline("audio-classification", model="<model-id>")',
        "Audio classifiers inherit dataset biases (speaker, channel); audit per-subgroup.",
    ),
    "CLIPModel": (
        "zero-shot-image-classification",
        "top-k accuracy over candidate label sets",
        'zs = pipeline("zero-shot-image-classification", model="<model-id>")',
        "Zero-shot accuracy is label-set-dependent: change the candidate labels and the ranking changes.",
    ),
    "ViTForImageClassification": (
        "image-classification",
        "top-1 / top-5 accuracy (calibrated per domain)",
        'vit = pipeline("image-classification", model="<model-id>")',
        "Vision models perform far below benchmark figures on out-of-distribution inputs; test the real distribution.",
    ),
    "Qwen2ForCausalLM": (
        "text-generation",
        "perplexity; task benchmarks; alignment evals for chat variants",
        'gen = pipeline("text-generation", model="<model-id>")',
        "Chat variants are alignment-tuned: benchmark refusal behavior and harmful-content handling as features.",
    ),
}

_KNOWN_LICENSES = (
    "apache-2.0", "mit", "bsd-3-clause", "bsd-2-clause", "cc-by-4.0",
    "cc-by-sa-4.0", "cc-by-nc-4.0", "lgpl-3.0", "gpl-3.0", "mozilla-2.0",
)


@dataclass
class ModelFacts:
    name: str
    config: dict
    license: str | None = None
    language: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str = "local"

    @property
    def model_type(self) -> str | None:
        return self.config.get("model_type")

    @property
    def architectures(self) -> list[str]:
        archs = self.config.get("architectures") or []
        if isinstance(archs, str):
            return [archs]
        return [str(a) for a in archs] if archs else []

    def task_info(self) -> tuple[str, ...] | None:
        for arch in self.architectures:
            if arch in ARCH_TASKS:
                return ARCH_TASKS[arch]
        return None


def _h(config: dict, *keys: str) -> int | None:
    """First present int field among keys (walks nested dicts for clip-style)."""
    for key in keys:
        raw = config.get(key)
        if isinstance(raw, (int, float)):
            return int(raw)
    for value in config.values():
        if isinstance(value, dict):
            hit = _h(value, *keys)
            if hit is not None:
                return hit
    return None


def estimate_params(facts: ModelFacts) -> int | None:
    """Order-of-magnitude parameter estimate from config geometry.

    Uses the standard transformer count 12*H^2*L plus embedding tables;
    returns None when the config has too little information. The estimate
    is documented as approximate, not a byte-exact count.
    """
    c = facts.config
    model_type = facts.model_type or ""
    hidden = _h(c, "hidden_size", "d_model", "n_embd")
    layers = _h(c, "num_hidden_layers", "n_layer", "decoder_layers", "encoder_layers")
    vocab = _h(c, "vocab_size", "n_vocab")
    if hidden is None or layers is None:
        return None

    base = 12 * hidden * hidden * layers
    if "whisper" in model_type:
        enc = _h(c, "encoder_layers", "num_hidden_layers") or layers
        dec = _h(c, "decoder_layers") or enc
        mel = _h(c, "num_mel_bins", 80)
        head = mel * hidden
        base = 12 * hidden * hidden * (enc + dec) + (vocab or 51865) * hidden + head
    elif "clip" in model_type:
        vh = _h(c.get("vision_config", {}), "hidden_size") or hidden
        vl = _h(c.get("vision_config", {}), "num_hidden_layers") or layers
        th = _h(c.get("text_config", {}), "hidden_size") or hidden
        tl = _h(c.get("text_config", {}), "num_hidden_layers") or layers
        base = 12 * vh * vh * vl + 12 * th * th * tl
        if vocab:
            base += vocab * th
    else:
        base += (vocab or 0) * hidden * 4  # token/type/position embeddings
    return base


def detect_license(root: Path | None, declared: str | None) -> str:
    """License truth = declared field, else LICENSE file sniff, else unknown."""
    if declared:
        return declared.strip()
    if root:
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
            lic_path = root / name
            if lic_path.exists():
                text = lic_path.read_text(encoding="utf-8", errors="replace")[:4000].lower()
                for known in _KNOWN_LICENSES:
                    if known in text:
                        return known
                return "custom (unrecognized)"
    return "unspecified"


def checklist_score(facts: ModelFacts, params: int | None) -> tuple[int, list[str]]:
    """0-100 documentation-completeness score with an actionable miss list."""
    score = 0
    missing: list[str] = []
    sections = [
        (facts.name and facts.name != "unnamed-model", 15, "model name"),
        (facts.license and facts.license not in ("unspecified", "custom (unrecognized)"), 15, "declared license"),
        (bool(facts.task_info()), 15, "task inference"),
        (params is not None, 15, "parameter estimate"),
        (bool(facts.architectures), 10, "architecture"),
        (bool(facts.language), 10, "language field"),
        (len(facts.tags) >= 2, 10, "at least 2 tags"),
        (bool(str(facts.config.get("model_type", ""))), 10, "model_type"),
    ]
    for ok, weight, label in sections:
        if ok:
            score += weight
        else:
            missing.append(label)
    if score >= 80:
        band = "A"
    elif score >= 60:
        band = "B"
    elif score >= 40:
        band = "C"
    else:
        band = "D"
    return band, missing


def render_card(facts: ModelFacts, params: int | None) -> str:
    """Deterministic markdown model card (no timestamps)."""
    task = facts.task_info()
    band, missing = checklist_score(facts, params)
    lines = [
        f"# {facts.name or 'unnamed-model'}",
        "",
        f"- **License:** {facts.license or 'unspecified'}",
        f"- **Model type:** {facts.model_type or 'unknown'}",
        f"- **Architectures:** {', '.join(facts.architectures) or 'unknown'}",
        f"- **Language:** {facts.language or 'unspecified'}",
        f"- **Parameters:** {f'{params:,} (estimated)' if params else 'not estimable from config'}",
        f"- **Checklist score:** {band}",
        "",
        "## Intended use",
        "",
    ]
    if task:
        lines += [
            f"- Task: `{task[0]}`",
            f"- Metrics: {task[1]}",
            "",
            "```python",
            task[2].replace("<model-id>", facts.name or "<model-id>"),
            "```",
            "",
        ]
    else:
        lines += [
            "- Task could not be inferred from the architecture; add a `pipeline_tag`/description.",
            "",
        ]
    lines += ["## Limitations and risks", ""]
    if task:
        lines += [f"- {task[3]}", ""]
    lines += [
        "- This card was generated from config facts; benchmark numbers,",
        "  training data details, and bias evaluations must be filled in by",
        "  the model author.",
        "",
        "## Metrics",
        "",
        f"- Recommended: {task[1] if task else 'task-specific (see Intended use)'}",
        "- _None reported yet._",
        "",
        "## Checklist (for the author)",
        "",
    ]
    if missing:
        lines += [f"- [ ] {m}" for m in missing]
    else:
        lines += ["- [x] All checklist items covered by generated content."]
    lines += ["", "_Generated by `card-forge`; deterministic given config and metadata._"]
    return "\n".join(lines)


# ------------------------------------------------------------------ diffing
def normalize_config(raw: dict) -> dict:
    """Flatten nested config dicts to dotted keys for stable diffing."""
    out: dict[str, object] = {}

    def walk(prefix: str, node: dict) -> None:
        for key, value in node.items():
            if key.startswith("_"):
                continue  # identity/metadata keys are not model configuration
            full = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                walk(full, value)
            else:
                out[full] = value

    walk("", raw)
    return out


@dataclass
class ConfigDiff:
    a_name: str
    b_name: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: dict[str, tuple[object, object]] = field(default_factory=dict)

    @property
    def changed_count(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def summary_line(self) -> str:
        return f"diff: {self.a_name} -> {self.b_name}: {len(self.changed)} changed, {len(self.added)} added, {len(self.removed)} removed"


def diff_configs(a: dict, b: dict) -> ConfigDiff:
    na, nb = normalize_config(a), normalize_config(b)
    d = ConfigDiff(a_name=str(a.get("_model_name", "a")), b_name=str(b.get("_model_name", "b")))
    d.added = sorted(k for k in nb if k not in na)
    d.removed = sorted(k for k in na if k not in nb)
    d.changed = {k: (na[k], nb[k]) for k in na if k in nb and na[k] != nb[k]}
    return d


def render_diff(d: ConfigDiff) -> str:
    lines = ["# Config diff", "", f"- `{d.a_name}` → `{d.b_name}`", f"- {d.changed_count} differences", ""]
    if d.added:
        lines += ["## Added keys"] + [f"- `{k}`" for k in d.added] + [""]
    if d.removed:
        lines += ["## Removed keys"] + [f"- `{k}`" for k in d.removed] + [""]
    if d.changed:
        lines += ["## Changed values", ""]
        for k, (old, new) in sorted(d.changed.items()):
            lines.append(f"- `{k}`: {json.dumps(old, sort_keys=True)} → {json.dumps(new, sort_keys=True)}")
        lines.append("")
    lines.append("_Generated by `card-forge`; deterministic given both configs._")
    return "\n".join(lines)