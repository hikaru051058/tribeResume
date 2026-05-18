"""JSON schema for targeted bullet patch outputs."""

PATCH_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "target_role",
        "focus",
        "overall_patch_strategy",
        "patches",
        "do_not_change",
        "missing_info_questions",
    ],
    "properties": {
        "target_role": {"type": "string"},
        "focus": {"type": "string"},
        "overall_patch_strategy": {"type": "string"},
        "patches": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "section",
                    "original_bullet",
                    "proposed_bullet",
                    "reason",
                    "evidence_preserved",
                    "evidence_added_from_existing_context",
                    "evidence_removed",
                    "risk_level",
                    "accept_recommendation",
                ],
                "properties": {
                    "section": {"type": "string"},
                    "original_bullet": {"type": "string"},
                    "proposed_bullet": {"type": "string"},
                    "reason": {"type": "string"},
                    "evidence_preserved": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_added_from_existing_context": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_removed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "accept_recommendation": {
                        "type": "string",
                        "enum": ["accept", "review", "reject"],
                    },
                },
            },
        },
        "do_not_change": {
            "type": "array",
            "items": {"type": "string"},
        },
        "missing_info_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

