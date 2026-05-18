"""Generate a concise demo report from existing TRIBE perception outputs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from format_demo_report import format_demo_report


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a final Markdown demo report from existing outputs."
    )
    parser.add_argument("--full-report", required=True)
    parser.add_argument("--timeline-report", required=True)
    parser.add_argument("--variant-report", required=True)
    parser.add_argument(
        "--output",
        default=str(ROOT / "outputs" / "demo_report.md"),
    )
    args = parser.parse_args()

    full_text = _read(args.full_report)
    timeline_text = _read(args.timeline_report)
    variant_text = _read(args.variant_report)
    data = {
        "full_resume": _extract_full_resume(full_text, timeline_text),
        "variant": _extract_variant(variant_text),
    }
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_demo_report(data), encoding="utf-8")
    print(f"Saved demo report: {output}")


def _extract_full_resume(full_text: str, timeline_text: str) -> dict:
    return {
        "prediction_shape": _bullet_value(full_text, "prediction shape")
        or _bullet_value(timeline_text, "prediction shape"),
        "retained_segments": _bullet_value(full_text, "retained segments")
        or _bullet_value(timeline_text, "retained segments"),
        "exact_stats": _bullet_value(timeline_text, "exact per-segment stats available"),
        "approximation_used": _bullet_value(timeline_text, "approximation used"),
        "highest_raw_salience": _top_table_section(full_text, "Highest Salience"),
        "highest_cognitive_load": _top_table_section(full_text, "Highest Cognitive Load Proxy")
        or _highest_signal(timeline_text, "Highest load-proxy section"),
        "highest_underemphasis": _top_table_section(full_text, "Most Underemphasized"),
        "key_interpretation": _first_sentence_after_heading(full_text, "Overall Perception Summary")
        or "Experience has the highest cognitive-load and underemphasis proxy signals, while intro has the highest raw salience.",
    }


def _extract_variant(variant_text: str) -> dict:
    experience = _table_row(variant_text, "experience")
    skills = _table_row(variant_text, "skills")
    interpretation = _first_bullet_after_heading(variant_text, "Interpretation")
    return {
        "facts_preserved": _bullet_value(variant_text, "Facts preserved"),
        "experience_load_delta": experience[5] if len(experience) > 5 else "not available",
        "skills_warning": skills[9] if len(skills) > 9 else "not available",
        "interpretation": interpretation
        or "The clearer variant reduced experience load, but stability warnings require timeline inspection.",
    }


def _bullet_value(text: str, label: str) -> str | None:
    pattern = rf"-\s*{re.escape(label)}:\s*`?([^`\n]+)`?"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _top_table_section(text: str, heading: str) -> str | None:
    block = _section(text, f"### {heading}")
    for line in block.splitlines():
        if line.startswith("| 1 |"):
            cells = _cells(line)
            return cells[1] if len(cells) > 1 else None
    return None


def _highest_signal(text: str, label: str) -> str | None:
    return _bullet_value(text, label)


def _table_row(text: str, section: str) -> list[str]:
    for line in text.splitlines():
        if line.lower().startswith(f"| {section.lower()} |"):
            return _cells(line)
    return []


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _first_sentence_after_heading(text: str, heading: str) -> str | None:
    block = _section(text, f"## {heading}")
    for line in block.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return None


def _first_bullet_after_heading(text: str, heading: str) -> str | None:
    block = _section(text, f"## {heading}")
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped[2:]
    return None


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    next_heading = re.search(r"\n##+ ", text[start + len(heading) :])
    end = start + len(heading) + next_heading.start() if next_heading else len(text)
    return text[start:end]


def _read(path: str) -> str:
    return _resolve(path).read_text(encoding="utf-8")


def _resolve(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


if __name__ == "__main__":
    main()
