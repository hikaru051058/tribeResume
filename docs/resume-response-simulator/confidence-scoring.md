# Confidence Scoring

## Definition

Confidence measures how well-supported the system's judgment is. It is not the same as an LLM saying it feels confident.

A high-confidence analysis means:

- The resume parsed cleanly.
- The evaluator cited exact evidence.
- The rubric scores are internally consistent.
- Multiple relevant personas agree.
- Required fields are present.
- Major claims are supported.
- Ambiguity and hallucination risk are low.

## Components

| Component | Meaning |
| --- | --- |
| Parser confidence | How reliably text, sections, dates, and layout were extracted. |
| Evidence coverage | Share of judgments backed by exact resume lines. |
| Rubric consistency | Whether scores align with written reasoning. |
| Persona agreement | Whether relevant evaluators converge. |
| Missing required fields | Penalty for missing dates, titles, skills, education, metrics, or target-role evidence. |
| Ambiguity penalty | Penalty for vague claims, unclear ownership, or confusing wording. |
| Unsupported claim penalty | Penalty for claims not supported by evidence. |

## Example Formula

```text
confidence =
  0.20 * parser_confidence
+ 0.25 * evidence_coverage
+ 0.20 * rubric_consistency
+ 0.15 * persona_agreement
+ 0.10 * required_field_score
+ 0.05 * ambiguity_score
+ 0.05 * supported_claim_score
```

Where penalty-derived scores are normalized:

```text
required_field_score = 1 - missing_required_fields_penalty
ambiguity_score = 1 - ambiguity_penalty
supported_claim_score = 1 - unsupported_claim_penalty
```

## Component Examples

### Parser Confidence

```json
{
  "parser_confidence": 0.87,
  "signals": {
    "sections_detected": true,
    "dates_detected": true,
    "tables_detected": false,
    "layout_preserved": true,
    "ambiguous_lines": [14, 37]
  }
}
```

### Evidence Coverage

```json
{
  "total_major_judgments": 12,
  "judgments_with_line_evidence": 10,
  "evidence_coverage": 0.83
}
```

### Persona Agreement

```json
{
  "persona_labels": {
    "technical_recruiter": "Good",
    "software_engineering_manager": "Mixed",
    "skeptical_reviewer": "Mixed",
    "ats_parser": "Good"
  },
  "persona_agreement": 0.71,
  "disagreement_summary": "Recruiter and ATS see a screenable resume, while engineering and skeptical reviewers flag weak ownership evidence."
}
```

## Full Confidence JSON Example

```json
{
  "confidence": {
    "score": 0.76,
    "level": "medium_high",
    "components": {
      "parser_confidence": 0.91,
      "evidence_coverage": 0.84,
      "rubric_consistency": 0.79,
      "persona_agreement": 0.68,
      "required_field_score": 0.82,
      "ambiguity_score": 0.70,
      "supported_claim_score": 0.75
    },
    "penalties": [
      {
        "type": "ambiguity",
        "severity": "medium",
        "evidence_lines": [28, 31],
        "reason": "Several bullets claim improvement without metric, baseline, or scope."
      },
      {
        "type": "unsupported_claim",
        "severity": "medium",
        "evidence_lines": [34],
        "reason": "The resume claims AI expertise but does not name models, data, evaluation, or deployment context."
      }
    ]
  }
}
```

## Confidence Labels

| Score | Label | Interpretation |
| ---: | --- | --- |
| 0.90-1.00 | Very high | Strong evidence and low ambiguity. |
| 0.75-0.89 | High | Mostly supported, minor uncertainty. |
| 0.55-0.74 | Medium | Useful analysis, but gaps affect certainty. |
| 0.35-0.54 | Low | Parsing, evidence, or ambiguity issues are significant. |
| 0.00-0.34 | Very low | Analysis should not be trusted without more input. |

