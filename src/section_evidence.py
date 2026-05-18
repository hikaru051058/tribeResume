"""Section-level evidence extraction for perception reports."""

from __future__ import annotations

import re

from evidence_extractor import (
    extract_named_evidence,
    extract_numeric_evidence,
    extract_technology_evidence,
)


SECTION_NAMES = {
    "intro",
    "contact",
    "education",
    "experience",
    "projects",
    "publications",
    "skills",
}

TOP_LEVEL_SECTION_NAMES = SECTION_NAMES - {"intro", "contact"}


def extract_section_text(resume_text: str, section_name: str) -> str:
    """Extract bounded text for a named resume section."""

    target = section_name.lower()
    if target in {"intro", "contact"}:
        section = next(
            (item for item in split_document_sections(resume_text) if item["name"] == "intro"),
            None,
        )
        return section["text"] if section else ""

    if target in {"coursework", "education / coursework"}:
        return extract_coursework_text(resume_text)

    for section in split_document_sections(resume_text):
        if section["name"] == target:
            return section["text"]
    return ""


def split_document_sections(text: str) -> list[dict]:
    """Split document text using heading boundaries only."""

    lines = text.splitlines()
    sections = []
    current_name = "intro"
    current_start = 1
    current_lines: list[str] = []

    def flush(end_line: int) -> None:
        if current_lines:
            sections.append(
                {
                    "name": current_name,
                    "start_line": current_start,
                    "end_line": end_line,
                    "text": "\n".join(current_lines).strip(),
                }
            )

    for index, line in enumerate(lines, start=1):
        heading = _top_level_heading(line)
        if heading:
            flush(index - 1)
            current_name = heading
            current_start = index
            current_lines = [line]
        else:
            current_lines.append(line)

    flush(len(lines))
    return [section for section in sections if section["text"]]


def extract_section_evidence(
    resume_text: str, section_name: str, max_items: int = 5
) -> list[str]:
    """Extract short evidence phrases for one report section."""

    section_text = extract_section_text(resume_text, section_name)
    evidence = []
    evidence.extend(extract_numeric_evidence(section_text))
    evidence.extend(extract_technology_evidence(section_text))
    evidence.extend(extract_named_evidence(section_text))
    if len(evidence) < max_items:
        evidence.extend(_short_representative_lines(section_text))
    return _unique(evidence)[:max_items]


def extract_coursework_text(resume_text: str) -> str:
    """Extract coursework only from bounded education text or real heading."""

    for section in split_document_sections(resume_text):
        if section["name"] == "coursework":
            return section["text"]
        if section["name"] == "education":
            lines = [
                line.strip()
                for line in section["text"].splitlines()
                if re.search(r"\b(?:relevant\s+)?coursework\b", line, flags=re.IGNORECASE)
            ]
            return "\n".join(lines)
    return ""


def _short_representative_lines(section_text: str) -> list[str]:
    lines = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip(" -•\t")
        if not line:
            continue
        if len(line) > 140:
            line = line[:137].rstrip() + "..."
        lines.append(line)
    return lines


def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()


def _top_level_heading(line: str) -> str | None:
    stripped = line.strip().strip(":")
    normalized = _normalize_heading(stripped)
    if normalized in TOP_LEVEL_SECTION_NAMES and _looks_like_heading(stripped):
        return normalized
    if normalized == "coursework" and _looks_like_heading(stripped):
        return normalized
    return None


def _looks_like_heading(line: str) -> bool:
    if not line:
        return False
    words = line.split()
    if len(words) > 3:
        return False
    if line.endswith(":"):
        return True
    return line.isupper() or line.istitle()


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", str(item).strip())
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
