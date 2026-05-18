"""Inspect TRIBE text extractor configuration without running prediction."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tribe_output_serializer import summarize_object, to_json_safe


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "outputs" / "tribe_text_extractor_inspection.json"
DEFAULT_MD = ROOT / "outputs" / "tribe_text_extractor_inspection.md"
SEARCH_TERMS = [
    "llama",
    "meta-llama",
    "Llama",
    "embedding",
    "tokenizer",
    "model_name",
    "pretrained",
    "hf",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect TRIBE text extractor config.")
    parser.add_argument("--cache-folder", default="./cache_probe")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    output_json = _resolve(args.output_json)
    output_md = _resolve(args.output_md)

    try:
        from tribev2.demo_utils import TribeModel

        model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=args.cache_folder,
            device=args.device,
        )
        inspection = inspect_model(model)
        inspection["status"] = "ok"
        inspection["cache_folder"] = args.cache_folder
        inspection["device"] = args.device
    except Exception as exc:
        inspection = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "cache_folder": args.cache_folder,
            "device": args.device,
        }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(to_json_safe(inspection), indent=2) + "\n", encoding="utf-8")
    output_md.write_text(format_markdown(inspection), encoding="utf-8")
    print(f"Saved inspection JSON: {output_json}")
    print(f"Saved inspection Markdown: {output_md}")


def inspect_model(model: Any) -> dict:
    data = getattr(model, "data", None)
    extractors = _extract_extractors(data)
    return {
        "model_summary": summarize_object(model),
        "data_summary": summarize_object(data),
        "extractors": extractors,
        "text_extractors": [
            item for item in extractors if "text" in item.get("name", "").lower()
        ],
        "search_hits": _search_object(model),
    }


def _extract_extractors(data: Any) -> list[dict]:
    candidates = []
    for attr in ["extractors", "_extractors", "features", "feature_extractors"]:
        value = getattr(data, attr, None)
        if value is not None:
            candidates.append((attr, value))

    results = []
    for attr, value in candidates:
        if isinstance(value, dict):
            iterable = value.items()
        elif isinstance(value, list | tuple):
            iterable = [(str(index), item) for index, item in enumerate(value)]
        else:
            iterable = [(attr, value)]
        for name, extractor in iterable:
            results.append(
                {
                    "container_attr": attr,
                    "name": str(name),
                    "summary": summarize_object(extractor),
                    "config_like_attributes": _config_attributes(extractor),
                }
            )
    return results


def _config_attributes(obj: Any) -> dict:
    config = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
        if not any(term.lower() in key.lower() for term in SEARCH_TERMS + ["config", "name"]):
            continue
        try:
            value = getattr(obj, key)
        except Exception:
            continue
        if callable(value):
            continue
        config[key] = summarize_object(value) if not isinstance(value, str | int | float | bool | type(None)) else value
    return config


def _search_object(obj: Any, path: str = "model", depth: int = 0, seen: set[int] | None = None) -> list[dict]:
    if seen is None:
        seen = set()
    if depth > 4 or id(obj) in seen:
        return []
    seen.add(id(obj))
    hits = []
    text = repr(obj)
    if _contains_search_term(text):
        hits.append({"path": path, "repr_preview": text[:500]})

    children = []
    if isinstance(obj, dict):
        children = [(str(key), value) for key, value in obj.items()]
    elif isinstance(obj, list | tuple):
        children = [(str(index), value) for index, value in enumerate(obj[:50])]
    elif hasattr(obj, "__dict__"):
        try:
            children = [(str(key), value) for key, value in vars(obj).items()]
        except Exception:
            children = []

    for key, value in children:
        child_path = f"{path}.{key}"
        if _contains_search_term(key) or _contains_search_term(repr(value)):
            hits.append({"path": child_path, "repr_preview": repr(value)[:500]})
        if not isinstance(value, str | int | float | bool | type(None)):
            hits.extend(_search_object(value, child_path, depth + 1, seen))
    return _dedupe_hits(hits)


def _contains_search_term(text: str) -> bool:
    return any(re.search(re.escape(term), text, flags=re.IGNORECASE) for term in SEARCH_TERMS)


def _dedupe_hits(hits: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for hit in hits:
        key = (hit["path"], hit["repr_preview"])
        if key not in seen:
            seen.add(key)
            deduped.append(hit)
    return deduped


def format_markdown(inspection: dict) -> str:
    lines = [
        "# TRIBE Text Extractor Inspection",
        "",
        f"Status: `{inspection.get('status')}`",
        "",
        "## Text Extractors",
        "",
    ]
    for item in inspection.get("text_extractors", []):
        lines.extend(
            [
                f"### {item.get('name', 'unknown')}",
                f"- Container: `{item.get('container_attr', '')}`",
                f"- Type: `{item.get('summary', {}).get('type', '')}`",
                "",
            ]
        )
    if not inspection.get("text_extractors"):
        lines.extend(["No extractor with `text` in its name was found.", ""])

    lines.extend(["## Search Hits", ""])
    for hit in inspection.get("search_hits", [])[:80]:
        lines.extend([f"- `{hit.get('path')}`: {hit.get('repr_preview')}", ""])
    if not inspection.get("search_hits"):
        lines.extend(["No configured search terms were found.", ""])

    if inspection.get("error"):
        lines.extend(["## Error", "", inspection["error"], ""])
    return "\n".join(lines)


def _resolve(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


if __name__ == "__main__":
    main()

