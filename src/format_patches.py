"""Markdown formatting for bullet patch suggestions."""

from __future__ import annotations


def format_patch_report(patch_result: dict) -> str:
    """Format patch JSON as a Markdown report."""

    lines = [
        "# Bullet Patch Suggestions",
        "",
        f"Target role: {patch_result.get('target_role', '')}",
        f"Focus: {patch_result.get('focus', '')}",
        "",
        "## Strategy",
        "",
        patch_result.get("overall_patch_strategy", ""),
        "",
    ]

    for patch in patch_result.get("patches", []):
        lines.extend(
            [
                f"## {patch.get('section', 'unknown')}",
                "",
                "Original:",
                f"> {patch.get('original_bullet', '')}",
                "",
                "Proposed:",
                f"> {patch.get('proposed_bullet', '')}",
                "",
                "Reason:",
                patch.get("reason", ""),
                "",
                "Evidence preserved:",
            ]
        )
        preserved = patch.get("evidence_preserved", [])
        lines.extend([f"- {item}" for item in preserved] or ["- None listed"])
        lines.extend(
            [
                "",
                "Evidence added from existing context:",
            ]
        )
        added = patch.get("evidence_added_from_existing_context", [])
        lines.extend([f"- {item}" for item in added] or ["- None"])
        lines.extend(
            [
                "",
                "Evidence removed:",
            ]
        )
        removed = patch.get("evidence_removed", [])
        lines.extend([f"- {item}" for item in removed] or ["- None"])
        lines.extend(
            [
                "",
                "Validation:",
            ]
        )
        validation = patch.get("validation", {})
        if validation:
            lines.extend(
                [
                    f"- Risk: {validation.get('risk_level', '')}",
                    f"- Valid: {validation.get('valid', '')}",
                    f"- Section scope: {validation.get('section_name') or 'unknown'}",
                    "- Issues:",
                ]
            )
            issues = _validation_issue_lines(validation)
            lines.extend([f"  - {item}" for item in issues] or ["  - None"])
        else:
            lines.append("- Not run")
        lines.extend(
            [
                "",
                f"Risk: {patch.get('risk_level', '')}",
                "",
                f"Recommendation: {patch.get('accept_recommendation', '')}",
                "",
            ]
        )

    lines.extend(["## Do Not Change", ""])
    lines.extend([f"- {item}" for item in patch_result.get("do_not_change", [])] or ["- None"])
    lines.extend(["", "## Missing Info Questions", ""])
    lines.extend(
        [f"- {item}" for item in patch_result.get("missing_info_questions", [])]
        or ["- None"]
    )
    return "\n".join(lines) + "\n"


def _validation_issue_lines(validation: dict) -> list[str]:
    lines = []
    for item in validation.get("cross_section_evidence", []):
        lines.append(f"Cross-section evidence: {item}")
    for item in validation.get("unsupported_added_evidence", []):
        lines.append(f"Unsupported added evidence: {item}")
    for item in validation.get("entity_drift", []):
        lines.append(f"Entity drift: {item}")
    for item in validation.get("issues", []):
        if item not in {"cross_section_evidence", "unsupported_added_evidence", "entity_drift"}:
            lines.append(item)
    return lines
