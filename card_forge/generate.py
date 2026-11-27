"""One module owns the path from config facts to a finished model card.

Callers hand over a config dict plus author metadata; fact building, the
parameter estimate, checklist scoring, markdown rendering and the JSON
payload all stay behind this interface. Config loading (a local file or a
live Hub fetch) remains the caller's adapter at this seam.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import estimate_params, facts_from, render_card, score_checklist


@dataclass(frozen=True)
class CardResult:
    """A finished card: its facts, score, markdown and JSON representation."""

    name: str
    model_type: str | None
    architectures: list[str]
    task: str | None
    license: str | None
    language: str | None
    tags: list[str]
    params_estimated: int | None
    checklist_band: str
    checklist_missing: list[str]
    markdown: str

    def as_dict(self) -> dict:
        """JSON-ready payload, stable across both config-source adapters."""
        return {
            "name": self.name,
            "model_type": self.model_type,
            "architectures": list(self.architectures),
            "task": self.task,
            "license": self.license,
            "language": self.language,
            "tags": list(self.tags),
            "params_estimated": self.params_estimated,
            "checklist_band": self.checklist_band,
            "checklist_missing": list(self.checklist_missing),
        }


def generate_card(
    config: dict,
    *,
    name: str | None = None,
    license_: str | None = None,
    language: str | None = None,
    tags: list[str] | None = None,
) -> CardResult:
    """Config source plus metadata in; one finished card result out."""
    facts = facts_from(config, name, license_, language, tags)
    params = estimate_params(facts)
    checklist = score_checklist(facts, params)
    task = facts.task_info()
    return CardResult(
        name=facts.name,
        model_type=facts.model_type,
        architectures=facts.architectures,
        task=task[0] if task else None,
        license=facts.license,
        language=facts.language,
        tags=list(facts.tags),
        params_estimated=params,
        checklist_band=checklist.band,
        checklist_missing=list(checklist.missing),
        markdown=render_card(facts, params, checklist),
    )
