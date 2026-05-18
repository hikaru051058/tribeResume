"""JSON schemas for local resume reviewer agents."""

REVIEWER_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "persona",
        "rating",
        "confidence",
        "first_impression",
        "strongest_signals",
        "weak_or_confusing_signals",
        "credibility_risks",
        "evidence_quotes",
        "suggested_fixes",
        "final_summary",
    ],
    "properties": {
        "persona": {"type": "string"},
        "rating": {
            "type": "string",
            "enum": ["Great", "Good", "Mixed", "Weak", "Bad"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "first_impression": {"type": "string"},
        "strongest_signals": {
            "type": "array",
            "items": {"type": "string"},
        },
        "weak_or_confusing_signals": {
            "type": "array",
            "items": {"type": "string"},
        },
        "credibility_risks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "evidence_quotes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["quote", "reason"],
                "properties": {
                    "quote": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "suggested_fixes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "final_summary": {"type": "string"},
    },
}

