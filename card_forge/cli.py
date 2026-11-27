"""card-forge CLI — generate cards and diff configs, keyless by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, core
from .core import (
    ARCH_TASKS,
    ConfigDiff,
    diff_configs,
    render_diff,
)
from .generate import generate_card

FIXTURES = Path(__file__).resolve().parent / "data" / "fixtures"
EXIT_OK, EXIT_NO_DEP, EXIT_ERROR = 0, 2, 1


def load_config(path: str | Path) -> dict:
    p = Path(path)
    if p.is_dir():
        p = p / "config.json"
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{p}: expected a JSON object (config dict)")
    raw.setdefault("_model_name", p.stem.replace("-config", ""))
    return raw


def fetch_hf_config(repo_id: str) -> dict:
    """Keyless live fetch of a Hub repo's config.json (optional extra)."""
    import importlib.util

    if importlib.util.find_spec("huggingface_hub") is None:
        raise RuntimeError(
            "live Hub fetch needs the optional dependency: "
            "pip install 'card-forge[live]' (installs huggingface-hub)"
        )
    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(repo_id=repo_id, filename="config.json")
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw.setdefault("_model_name", repo_id.split("/")[-1])
        return raw
    except Exception as exc:  # network/model dependent
        raise RuntimeError(f"failed to fetch {repo_id!r} from the Hub: {exc}") from exc


def facts_from(config: dict, name: str | None, license_: str | None, language: str | None, tags: list[str] | None) -> core.ModelFacts:
    """Backwards-compatible public adapter to core.facts_from."""
    return core.facts_from(config, name, license_, language, tags)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="card-forge",
        description="Generate complete Hugging Face model cards from config facts; diff configs between revisions.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate a model card (default: bundled demo fixture)")
    g.add_argument("target", nargs="?", help="config.json path, model dir, or (--hf) repo id")
    g.add_argument("--hf", metavar="REPO_ID", help="fetch config from the live Hub (needs card-forge[live])")
    g.add_argument("--name", default=None)
    g.add_argument("--license", dest="license_", default=None)
    g.add_argument("--language", default=None)
    g.add_argument("--tag", action="append", default=None, help="extra tag (repeatable)")
    g.add_argument("--out", default=None, help="write card markdown to a file")
    g.add_argument("--format", choices=("markdown", "json"), default="markdown")

    d = sub.add_parser("diff", help="diff two model configs (paths, dirs, or --hf ids)")
    d.add_argument("a", nargs="?", default=None)
    d.add_argument("b", nargs="?", default=None)
    d.add_argument("--a-hf", metavar="REPO_ID")
    d.add_argument("--b-hf", metavar="REPO_ID")
    d.add_argument("--format", choices=("markdown", "json"), default="markdown")

    sub.add_parser("demo", help="generate the bundled demo card")
    sub.add_parser("tasks", help="list known architecture -> task mappings")
    return p


def _load_for_diff(a: str | None, b: str | None, a_hf: str | None, b_hf: str | None) -> tuple[dict, dict]:
    if a_hf and b_hf:
        return fetch_hf_config(a_hf), fetch_hf_config(b_hf)
    if a_hf or b_hf:
        raise ValueError("diff needs both sides as paths or both sides as --*-hf ids")
    if not (a and b):
        raise ValueError("diff needs two config paths (or two --*-hf ids)")
    return load_config(a), load_config(b)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "tasks":
        for arch, (task, metrics, _snippet, _lim) in sorted(ARCH_TASKS.items()):
            print(f"{arch:<42} {task:<32} {metrics}")
        return EXIT_OK

    if args.command == "demo":
        cfg = load_config(FIXTURES / "bert-tiny-config.json")
        meta = json.loads((FIXTURES / "demo-meta.json").read_text(encoding="utf-8"))
        result = generate_card(
            cfg,
            name=meta.get("name"),
            license_=meta.get("license"),
            language=meta.get("language"),
            tags=meta.get("tags"),
        )
        print(result.markdown)
        return EXIT_OK

    if args.command == "generate":
        try:
            if args.hf:
                cfg = fetch_hf_config(args.hf)
            elif args.target:
                cfg = load_config(args.target)
            else:
                cfg = load_config(FIXTURES / "bert-tiny-config.json")
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_ERROR
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_NO_DEP

        declared = args.license_
        result = generate_card(
            cfg,
            name=args.name,
            license_=declared,
            language=args.language,
            tags=args.tag,
        )
        if args.format == "json":
            print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        else:
            if args.out:
                Path(args.out).write_text(result.markdown, encoding="utf-8")
                print(f"wrote {args.out}")
            else:
                print(result.markdown)
        return EXIT_OK

    if args.command == "diff":
        try:
            ca, cb = _load_for_diff(args.a, args.b, args.a_hf, args.b_hf)
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_ERROR
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_NO_DEP
        d = diff_configs(ca, cb)
        if args.format == "json":
            print(json.dumps(diff_as_dict(d), indent=2, sort_keys=True))
        else:
            print(render_diff(d))
        return EXIT_OK

    return EXIT_ERROR


def diff_as_dict(d: ConfigDiff) -> dict:
    return {
        "a": d.a_name,
        "b": d.b_name,
        "changed": {k: {"old": old, "new": new} for k, (old, new) in d.changed.items()},
        "added": d.added,
        "removed": d.removed,
    }


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())