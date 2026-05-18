# API Design

## Overview

The API should support uploading resumes, running persona analyses, comparing versions, rewriting bullets, matching jobs, and fetching stored analyses.

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
  "overall_response": "Good",
  "confidence_score": 0.82,
  "created_at": "2026-05-17T10:32:00Z"
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

Analyze a resume with selected personas.

Request:

```json
{
  "resume_id": "res_123",
  "target_role": "Backend Software Engineer",
  "job_description": "We are looking for a backend engineer...",
  "personas": [
    "technical_recruiter",
    "software_engineering_manager",
    "skeptical_reviewer",
    "ats_parser"
  ],
  "include_rewrites": true
}
```

Response:

```json
{
  "analysis_id": "ana_123",
  "overall_response": "Mixed",
  "confidence_score": 0.76,
  "persona_results": [
    {
      "persona": "technical_recruiter",
      "overall_response": "Good",
      "role_fit_score": 80,
      "first_impression_10_seconds": "Likely screenable, with relevant backend keywords and clear experience."
    },
    {
      "persona": "software_engineering_manager",
      "overall_response": "Mixed",
      "role_fit_score": 68,
      "first_impression_10_seconds": "Relevant work is present, but ownership and production impact are under-specified."
    }
  ],
  "top_findings": [
    {
      "type": "weak_signal",
      "message": "Several bullets describe tasks without measurable outcomes.",
      "evidence_lines": [24, 28, 31]
    }
  ]
}
```

## POST /v1/resumes/compare

Compare multiple resume versions.

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

Generate targeted rewrites.

Request:

```json
{
  "resume_id": "res_123",
  "target_role": "Backend Software Engineer",
  "line_ids": [24, 25],
  "rewrite_goal": "Increase engineering manager confidence without adding unsupported claims"
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

