# Examples

## Sample Resume Snippet

```text
18 Experience
19 Software Engineer Intern, Acme Health
20 June 2025 - August 2025
21 Worked on backend APIs for patient onboarding.
22 Improved system performance and user experience.
23 Used AI to automate document review.
24 Collaborated with engineering team on database tasks.
```

## Sample Simulated Output

```json
{
  "overall_response": "Mixed",
  "first_impression_10_seconds": "The candidate has relevant engineering exposure, but the bullets are too vague to establish strong ownership or technical depth.",
  "strongest_signals": [
    {
      "signal": "Backend internship experience",
      "evidence_lines": [19, 21],
      "why_it_matters": "The candidate has direct software engineering experience in a domain context."
    }
  ],
  "weak_or_confusing_signals": [
    {
      "issue": "Impact is generic",
      "evidence_lines": [22],
      "why_it_matters": "The reader cannot tell what changed, by how much, or because of what technical work."
    }
  ],
  "credibility_risks": [
    {
      "risk": "Unsupported AI claim",
      "evidence_lines": [23],
      "why_it_matters": "The line does not name the model, data, evaluation, workflow, or user impact."
    }
  ]
}
```

## Before And After Bullet Rewrites

### Example 1: Backend API Bullet

Before:

```text
Worked on backend APIs for patient onboarding.
```

After:

```text
Built and maintained patient onboarding REST API endpoints, coordinating with frontend and database changes to support account setup workflows.
```

Why it helps:

- Adds ownership.
- Names the system boundary.
- Explains product context.
- Does not invent metrics.

### Example 2: Impact Bullet

Before:

```text
Improved system performance and user experience.
```

After, if the user can verify metrics:

```text
Reduced onboarding API latency by 32% by optimizing PostgreSQL queries and removing duplicate validation calls.
```

After, conservative version without metrics:

```text
Improved onboarding API responsiveness by optimizing PostgreSQL queries and removing duplicate validation calls.
```

## Recruiter Vs Engineering Manager Reactions

### Technical Recruiter Reaction

```json
{
  "persona": "technical_recruiter",
  "overall_response": "Good",
  "first_impression_10_seconds": "Relevant software engineering internship with backend, database, and AI keywords.",
  "positive_signals": [
    "Software Engineer Intern title",
    "Backend API experience",
    "Database exposure",
    "AI-related keyword"
  ],
  "concerns": [
    "Impact is not quantified",
    "Skills section would need to confirm stack"
  ]
}
```

### Engineering Manager Reaction

```json
{
  "persona": "software_engineering_manager",
  "overall_response": "Mixed",
  "first_impression_10_seconds": "The experience is relevant, but the resume does not show enough ownership, technical decisions, or measurable production impact.",
  "positive_signals": [
    "Worked on backend APIs",
    "Exposure to database tasks"
  ],
  "concerns": [
    "No API scale or reliability context",
    "No details on database work",
    "AI claim lacks technical substance"
  ]
}
```

## Bad Resume Response Example

Input snippet:

```text
Created revolutionary AI platform that transformed operations.
Worked with many technologies to improve everything.
Led multiple teams and delivered huge impact.
```

Simulated response:

```json
{
  "overall_response": "Bad",
  "first_impression_10_seconds": "The resume sounds inflated and unsupported. The claims are broad, but there is no concrete evidence of role, scope, technology, metrics, or ownership.",
  "credibility_risks": [
    "Revolutionary AI platform is not explained.",
    "Many technologies is too vague to evaluate.",
    "Led multiple teams has no team size, title, or context.",
    "Huge impact has no metric or outcome."
  ],
  "recommended_action": "Replace broad claims with specific project, technology, ownership, and measurable outcome details."
}
```

## Great Resume Response Example

Input snippet:

```text
Built a FastAPI service that processed 1.2M monthly eligibility checks for a healthcare onboarding workflow.
Reduced p95 API latency from 840ms to 310ms by adding Redis caching and optimizing PostgreSQL indexes.
Created integration tests for 14 critical onboarding paths, reducing escaped validation bugs by 38%.
```

Simulated response:

```json
{
  "overall_response": "Great",
  "first_impression_10_seconds": "This reads as credible backend engineering work with clear ownership, scale, technical choices, and measurable impact.",
  "strongest_signals": [
    "Production scale is clear.",
    "Technical implementation is specific.",
    "Performance improvement has baseline and result.",
    "Testing work connects to product reliability."
  ],
  "confidence_score": 0.91,
  "why_confidence_is_high": "Most claims include concrete evidence: system, scale, technical method, and outcome."
}
```

