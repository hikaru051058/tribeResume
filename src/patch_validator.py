"""Section-aware validation for resume bullet patches."""

from __future__ import annotations

import re


SECTION_HEADINGS = {
    "summary",
    "education",
    "experience",
    "work experience",
    "professional experience",
    "projects",
    "technical projects",
    "skills",
    "technical skills",
    "publications",
    "awards",
    "certifications",
}

RISK_ORDER = {"low": 1, "medium": 2, "high": 3}

ENTITY_DOMAINS = {
    "arin": {"arin", "cosmetic", "cosmetics", "social", "recommendation", "funding"},
    "sem": {"sem", "medical", "clinical", "reporting", "healthcare", "patient"},
    "opaque hand": {"opaque", "prosthetic", "hand", "tensorflow", "swiftui", "uikit"},
    "niftiq": {"niftiq", "blockchain", "ticketing", "ticket", "web3"},
}


def split_resume_into_sections(text: str) -> list[dict]:
    """Split a resume into local sections, including company/project chunks."""

    lines = text.splitlines()
    sections = []
    current_name = "intro"
    current_start = 1
    current_lines: list[str] = []
    parent_heading = "intro"

    def flush(end_index: int) -> None:
        if current_lines or not sections:
            sections.append(
                {
                    "section_name": current_name,
                    "start_index": current_start,
                    "end_index": end_index,
                    "text": "\n".join(current_lines).strip(),
                }
            )

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            current_lines.append(line)
            continue

        heading = _section_heading(stripped)
        local_chunk = _local_chunk_heading(stripped, parent_heading, lines, index)
        if heading or local_chunk:
            flush(index - 1)
            if heading:
                parent_heading = heading
                current_name = heading
            else:
                current_name = f"{parent_heading} / {local_chunk}"
            current_start = index
            current_lines = [line]
            continue

        current_lines.append(line)

    flush(len(lines))
    return [section for section in sections if section["text"]]


def find_section_for_bullet(resume_text: str, bullet: str) -> dict | None:
    """Find the local section containing a bullet."""

    bullet_norm = _normalize_text(_strip_bullet_marker(bullet))
    if not bullet_norm:
        return None
    for section in split_resume_into_sections(resume_text):
        section_norm = _normalize_text(section["text"])
        if bullet_norm in section_norm:
            return section
    return None


def validate_patch_evidence_scope(resume_text: str, patch: dict) -> dict:
    """Validate whether a patch borrows evidence safely from the same section."""

    original_bullet = str(patch.get("original_bullet", ""))
    proposed_bullet = str(patch.get("proposed_bullet", ""))
    section = find_section_for_bullet(resume_text, original_bullet)
    section_text = section["text"] if section else ""

    issues = []
    cross_section_evidence = []
    unsupported_added_evidence = []
    entity_drift = []

    if section is None:
        issues.append("original_bullet_not_found")

    for evidence in _as_list(patch.get("evidence_preserved")):
        if not _contains_text(original_bullet, evidence) and not _contains_text(section_text, evidence):
            issues.append(f"preserved_evidence_not_in_original_section: {evidence}")

    for evidence in _as_list(patch.get("evidence_added_from_existing_context")):
        if _contains_text(section_text, evidence):
            continue
        if _contains_text(resume_text, evidence):
            cross_section_evidence.append(evidence)
        else:
            unsupported_added_evidence.append(evidence)

    entity_drift = _detect_entity_drift(original_bullet, proposed_bullet, section_text)

    if cross_section_evidence:
        issues.append("cross_section_evidence")
    if unsupported_added_evidence:
        issues.append("unsupported_added_evidence")
    if entity_drift:
        issues.append("entity_drift")

    risk_level = "low"
    if unsupported_added_evidence:
        risk_level = "medium"
    if cross_section_evidence or entity_drift or section is None:
        risk_level = "high"

    return {
        "valid": not issues,
        "risk_level": risk_level,
        "issues": issues,
        "cross_section_evidence": cross_section_evidence,
        "unsupported_added_evidence": unsupported_added_evidence,
        "entity_drift": entity_drift,
        "section_name": section["section_name"] if section else None,
    }


def _section_heading(line: str) -> str | None:
    normalized = _normalize_heading(line)
    return normalized if normalized in SECTION_HEADINGS else None


def _local_chunk_heading(line: str, parent_heading: str, lines: list[str], index: int) -> str | None:
    if parent_heading not in {
        "experience",
        "work experience",
        "professional experience",
        "projects",
        "technical projects",
    }:
        return None
    if _line_is_bullet(line) or _section_heading(line):
        return None
    if len(line.split()) > 12:
        return None

    next_lines = lines[index : min(len(lines), index + 4)]
    has_nearby_bullet = any(_line_is_bullet(next_line) for next_line in next_lines)
    has_entity_cue = any(cue in line.lower() for cue in ["ltd", "inc", "llc", "solutions", "arin", "sem", "opaque", "niftiq"])
    if has_nearby_bullet or has_entity_cue:
        return line.strip().strip(":")
    return None


def _line_is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*•]|[0-9]+[.)])\s+", line))


def _strip_bullet_marker(text: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|[0-9]+[.)])\s+", "", text.strip())


def _normalize_heading(text: str) -> str:
    return re.sub(r"[^a-z0-9 /]+", "", text.lower()).strip().strip(":")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.%$+/# -]+", " ", text.lower())).strip()


def _contains_text(haystack: str, needle: str) -> bool:
    needle_norm = _normalize_text(str(needle))
    if not needle_norm:
        return False
    return needle_norm in _normalize_text(haystack)


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value:
        return [str(value)]
    return []


def _detect_entity_drift(original_bullet: str, proposed_bullet: str, section_text: str) -> list[str]:
    original_scope = f"{original_bullet}\n{section_text}".lower()
    proposed = proposed_bullet.lower()
    original_domains = {
        entity
        for entity, markers in ENTITY_DOMAINS.items()
        if any(marker in original_scope for marker in markers)
    }
    proposed_domains = {
        entity
        for entity, markers in ENTITY_DOMAINS.items()
        if any(marker in proposed for marker in markers)
    }
    drift = []
    for entity in sorted(proposed_domains - original_domains):
        drift.append(
            f"proposed bullet introduces {entity} domain/entity outside the original bullet section"
        )
    return drift

