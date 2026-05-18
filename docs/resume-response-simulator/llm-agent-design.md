# LLM Agent Design

## Agent Inputs

Each evaluator agent receives:

- Parsed resume text.
- Structured candidate profile.
- Evidence index with line numbers.
- Optional target role.
- Optional job description.
- Persona-specific rubric.
- Required JSON output schema.

## Evaluator Agents

| Agent | Primary Lens |
| --- | --- |
| Technical recruiter | Screenability, role keywords, seniority, obvious fit. |
| Software engineering manager | Ownership, technical depth, production impact, team fit. |
| AI/ML reviewer | Model details, data, evaluation, research or applied ML credibility. |
| Graduate admissions reviewer | Academic preparation, research potential, motivation, fit. |
| Skeptical reviewer | Inflated claims, unsupported impact, ambiguity, credibility gaps. |
| ATS parser | Machine-readable structure, sections, dates, skills, title extraction. |
| Startup founder / technical cofounder | Ownership, speed, ambiguity tolerance, product impact. |
| General non-technical HR reader | Clarity, professionalism, understandable story. |

## Shared Prompt Template

```text
You are simulating the first-pass reaction of a {persona_name}.

Task:
Evaluate the resume for {target_context}. Do not provide generic resume advice.
Simulate how this reader would likely perceive the document under time pressure.

Inputs:
- Resume text with line numbers: {resume_lines}
- Structured candidate profile: {candidate_profile}
- Target role or program: {target_role}
- Job description or criteria: {job_description}
- Rubric: {persona_rubric}

Rules:
- Cite exact resume lines for every major judgment.
- Separate strong evidence from weak or unsupported claims.
- Do not invent facts.
- Mark missing information explicitly.
- Use the response labels: Great, Good, Mixed, Weak, Bad.
- Return only valid JSON matching the schema.
```

## Persona Prompt Additions

### Technical Recruiter

```text
Prioritize screenability, role keyword match, seniority match, recognizable scope,
clear titles, dates, skills, and whether this candidate should move to a phone screen.
```

### Software Engineering Manager

```text
Prioritize evidence of ownership, production systems, debugging, tradeoffs,
collaboration, reliability, code quality, and measurable engineering impact.
```

### AI/ML Reviewer

```text
Prioritize technical specificity: model types, datasets, evaluation metrics,
baselines, deployment context, error analysis, research depth, and whether AI/ML
claims are credible.
```

### Graduate Admissions Reviewer

```text
Prioritize research potential, academic preparation, publications, projects,
recommendation-relevant evidence, intellectual direction, and fit with a program.
```

### Skeptical Reviewer

```text
Assume some claims may be inflated. Identify unsupported scope, vague impact,
generic buzzwords, suspicious metrics, unclear ownership, and missing evidence.
```

### ATS Parser

```text
Evaluate machine readability. Focus on section detection, dates, titles,
company names, skills extraction, keyword match, formatting risk, and parse failures.
```

### Startup Founder / Technical Cofounder

```text
Prioritize autonomy, product sense, shipping speed, customer impact, broad ownership,
technical range, and ability to operate with ambiguity.
```

### General Non-Technical HR Reader

```text
Prioritize clarity, professionalism, simple narrative, understandable achievements,
consistency, and whether the resume avoids confusing technical overload.
```

## Expected JSON Output Schema

```json
{
  "persona": "software_engineering_manager",
  "overall_response": "Mixed",
  "first_impression_10_seconds": "Clear backend experience, but impact and ownership are under-specified.",
  "role_fit_score": 72,
  "confidence_score": 0.78,
  "strongest_signals": [
    {
      "signal": "Production backend experience",
      "evidence_lines": [22, 23],
      "explanation": "The resume describes API and database work in a production workflow."
    }
  ],
  "weak_or_confusing_signals": [
    {
      "issue": "Impact is vague",
      "evidence_lines": [25],
      "explanation": "The line says performance improved but gives no metric, baseline, or scope."
    }
  ],
  "credibility_risks": [
    {
      "risk": "Unsupported AI claim",
      "evidence_lines": [31],
      "severity": "medium"
    }
  ],
  "missing_information": [
    "Team size",
    "Traffic or user scale",
    "Testing or reliability evidence"
  ],
  "suggested_rewrites": [
    {
      "original_line": 25,
      "rewrite": "Reduced API response latency by 35% by adding PostgreSQL indexes and caching repeated account lookups.",
      "requires_user_verification": true
    }
  ]
}
```

## Scoring Dimensions

| Dimension | Description |
| --- | --- |
| Clarity | Can the reader understand the candidate quickly? |
| Credibility | Are claims specific and supported? |
| Role fit | Does the evidence match the target role? |
| Technical depth | Is the work technically meaningful for the role? |
| Impact | Are outcomes measurable or concrete? |
| Signal density | How much useful evidence appears per page? |
| Risk | Are there confusing, inflated, or missing claims? |

## Agent Disagreement And Aggregation

Disagreement is useful. The system should preserve it instead of flattening every review into one score.

Aggregation approach:

- Compute per-persona response labels and scores.
- Identify consensus strengths and weaknesses.
- Highlight disagreements.
- Weight personas based on target context.
- Produce an overall response only after showing persona-level results.

Example weighting for a backend engineering role:

| Persona | Weight |
| --- | ---: |
| Software engineering manager | 0.35 |
| Technical recruiter | 0.25 |
| Skeptical reviewer | 0.15 |
| ATS parser | 0.15 |
| General HR reader | 0.10 |

