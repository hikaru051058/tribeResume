"""JSON schema for local Ollama resume rewrite outputs."""

REWRITE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rewrite_mode",
        "revised_resume_text",
        "major_changes",
        "removed_or_simplified_claims",
        "risks_or_assumptions",
        "preserved_evidence",
        "removed_evidence",
        "bullet_level_changes",
        "safety_warnings",
        "rewrite_confidence",
    ],
    "properties": {
        "rewrite_mode": {"type": "string", "enum": ["surgical", "full"]},
        "revised_resume_text": {"type": "string"},
        "major_changes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "removed_or_simplified_claims": {
            "type": "array",
            "items": {"type": "string"},
        },
        "risks_or_assumptions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "preserved_evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
        "removed_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["evidence", "reason"],
                "properties": {
                    "evidence": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "bullet_level_changes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["original", "revised", "reason", "evidence_preserved"],
                "properties": {
                    "original": {"type": "string"},
                    "revised": {"type": "string"},
                    "reason": {"type": "string"},
                    "evidence_preserved": {"type": "boolean"},
                },
            },
        },
        "safety_warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
        "rewrite_confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}
