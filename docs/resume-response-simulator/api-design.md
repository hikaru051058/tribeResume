# API Design

## Overview

This is a future API sketch. The current implementation is CLI-first and TRIBE-first.

The API should prioritize the current perception-report workflow:

1. Upload and parse a document.
2. Build synthetic reading events.
3. Attach or generate TRIBE prediction artifacts.
4. Run timeline and section-level feature extraction.
5. Generate a cautious perception report.
6. Optionally run reviewer-agent comparison, fusion, patch suggestions, or variant comparison.

Persona analyses, rewriting, and job matching are optional application-layer endpoints, not the core product.

## Data Models

### Resume

```json
{
  "resume_id": "res_123",
  "filename": "resume.pdf",
  "content_type": "application/pdf",
  "created_at": "2026-05-17T10:30:00Z",
  "parser_status": "complete",
  "parser_confidence": 0.91
}
```

### Analysis

```json
{
  "analysis_id": "ana_123",
  "resume_id": "res_123",
  "target_role": "Backend Software Engineer",
  "analysis_type": "perception_report",
  "perception_source": "real_tribe",
  "prediction_shape": [182, 20484],
  "created_at": "2026-05-17T10:32:00Z"
}
```

### Perception Report

```json
{
  "report_id": "per_123",
  "resume_id": "res_123",
  "perception_source": "real_tribe",
  "important_caution": [
    "Real TRIBE checkpoint output from synthetic reading events.",
    "No human was scanned.",
    "This is not a hiring prediction."
  ],
  "section_level_signals": [
    {
      "section": "experience",
      "salience_proxy": 0.71,
      "position_normalized_salience": 0.84,
      "cognitive_load_proxy": 0.91,
      "underemphasis_proxy": 0.88,
      "evidence_phrases": ["130,000+ reports", "~30% workload reduction"]
    }
  ]
}
```

### Persona Result

```json
{
  "persona": "technical_recruiter",
  "overall_response": "Good",
  "first_impression_10_seconds": "Screenable backend candidate with clear skills, but impact details are thin.",
  "role_fit_score": 78,
  "confidence_score": 0.84
}
```

## POST /v1/resumes/upload

Upload a resume file.

Request:

```http
POST /v1/resumes/upload
Content-Type: multipart/form-data
```

Fields:

- `file`: PDF, DOCX, TXT, or Markdown.
- `source`: optional source label.

Response:

```json
{
  "resume_id": "res_123",
  "status": "uploaded",
  "parser_status": "queued"
}
```

## POST /v1/resumes/analyze

Generate the primary perception analysis for a resume.

Request:

```json
{
  "resume_id": "res_123",
  "target_role": "Backend Software Engineer",
  "perception_source": "real_tribe",
  "timeline_analysis_id": "timeline_123",
  "include_reviewer_comparison": false
}
```

Response:

```json
{
  "analysis_id": "ana_123",
  "perception_source": "real_tribe",
  "confidence": {
    "text_review_confidence": null,
    "perception_signal_confidence": 0.5,
    "fusion_confidence": null
  },
  "proxy_rankings": {
    "highest_cognitive_load_proxy": [
      {"section": "experience", "value": 0.91}
    ]
  },
  "section_level_signals": [
    {
      "section": "experience",
      "signal_type": "high_cognitive_load_proxy",
      "evidence_phrases": ["130,000+ reports", "~30% workload reduction"],
      "suggestion": "Inspect whether dense metrics and technologies can be split without removing evidence."
    }
  ]
}
```

## POST /v1/resumes/compare

Compare multiple resume versions. In the current framing, comparison should prefer perception proxy and controlled-variant comparisons before making editing recommendations.

Request:

```json
{
  "resume_ids": ["res_123", "res_456"],
  "target_role": "AI/ML Engineer",
  "personas": ["technical_recruiter", "ai_ml_reviewer", "skeptical_reviewer"]
}
```

Response:

```json
{
  "comparison_id": "cmp_123",
  "winner_resume_id": "res_456",
  "winner_reason": "Version B provides clearer ML project evidence, metrics, and role alignment.",
  "persona_winners": {
    "technical_recruiter": "res_456",
    "ai_ml_reviewer": "res_456",
    "skeptical_reviewer": "res_123"
  },
  "tradeoffs": [
    "Version B is stronger for ML specificity but slightly denser."
  ]
}
```

## POST /v1/resumes/rewrite

Generate targeted rewrites. This is optional and should never be the default report behavior.

Request:

```json
{
  "resume_id": "res_123",
  "target_role": "Backend Software Engineer",
  "line_ids": [24, 25],
  "mode": "surgical",
  "allow_remove_gpa": false,
  "rewrite_goal": "Improve scanability without adding or removing concrete evidence"
}
```

Response:

```json
{
  "rewrites": [
    {
      "line_id": 24,
      "original": "Worked on APIs for onboarding.",
      "rewrite": "Built and maintained onboarding REST APIs in Node.js and PostgreSQL, improving account setup reliability for customer support workflows.",
      "requires_user_verification": true,
      "evidence_removed": [],
      "improvement_reason": "Adds ownership, stack, and product context while avoiding invented metrics."
    }
  ]
}
```

## POST /v1/jobs/match

Match a resume against a job description.

Request:

```json
{
  "resume_id": "res_123",
  "job_description": "Required: Python, distributed systems, AWS...",
  "target_company_context": "B2B SaaS startup"
}
```

Response:

```json
{
  "match_score": 74,
  "response_label": "Good",
  "matched_requirements": [
    {
      "requirement": "Python",
      "evidence_lines": [12, 33]
    }
  ],
  "gaps": [
    {
      "requirement": "AWS",
      "severity": "medium",
      "recommendation": "Add evidence of AWS work if accurate."
    }
  ]
}
```

## GET /v1/analyses/{analysis_id}

Fetch a stored analysis.

Response:

```json
{
  "analysis_id": "ana_123",
  "resume_id": "res_123",
  "overall_response": "Mixed",
  "confidence": {
    "score": 0.76,
    "level": "medium_high"
  },
  "persona_results": [],
  "findings": [],
  "rewrites": []
}
```
