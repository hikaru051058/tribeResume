# Ollama Reviewer Agents

## Purpose

The Ollama layer provides local LLM reviewer agents for semantic resume feedback, explanation, and comparison. It simulates how different evaluators may react to a resume while requiring every major judgment to cite evidence from the resume text.

Ollama reviewer agents are baseline/comparison and explanation tools. They are not the unique core system by themselves.

The corrected architecture treats TRIBE v2 as the core experimental perception layer and Ollama as the interpretation/explanation layer. TRIBE v2 is still not used to directly judge resume quality.

## Why Local LLMs Are Good Enough For MVP Testing

Local models are useful for early product testing because they are:

- Free to run after setup.
- Private by default when run locally.
- Fast enough for short resumes and six reviewer personas.
- Good enough to test prompts, schemas, aggregation, and UX.
- Easy to swap between faster and stronger models.

Recommended starting points:

- `llama3.1:8b` for fast testing.
- `qwen3:14b` for deeper critique where quality matters.

## Profile Guidance

| Profile | Use Case |
| --- | --- |
| `fast` | Quick local checks while editing prompts or code. Uses `llama3.1:8b`. |
| `balanced` | Default profile for normal reviews. Uses `llama3.1:8b` for faster screeners and `qwen3:14b` for deeper critique agents. |
| `deep` | Highest local review depth. Uses `qwen3:14b` for every reviewer. |
| `adaptive` | Fast first pass with selective escalation to `qwen3:14b` when needed. |

Install the recommended models:

```bash
ollama pull qwen3:14b
ollama pull llama3.1:8b
```

## Limitations

Local models can still:

- Miss subtle resume issues.
- Overrate vague claims.
- Produce inconsistent ratings across runs.
- Cite incomplete evidence.
- Struggle with strict JSON unless constrained.
- Reflect bias from training data.

The system should treat outputs as simulated evaluator feedback, not real hiring predictions.

## Agent List

| Agent | Purpose |
| --- | --- |
| Technical recruiter | Fast screenability, keywords, titles, dates, role fit. |
| Software engineering manager | Ownership, technical depth, production impact. |
| AI/ML reviewer | ML specificity, models, data, metrics, baselines. |
| Graduate admissions reviewer | Academic preparation, project depth, research potential. |
| Skeptical reviewer | Unsupported claims, inflated wording, ambiguity. |
| ATS parser | Machine readability, sections, dates, skills extraction. |

## Scoring Dimensions

- Clarity.
- Credibility.
- Role fit.
- Evidence strength.
- Technical depth.
- Impact.
- Missing information.
- Parsing or formatting risk.

Ratings:

- Great.
- Good.
- Mixed.
- Weak.
- Bad.

## JSON Output Schema

```json
{
  "persona": "technical_recruiter",
  "rating": "Good",
  "confidence": 0.78,
  "first_impression": "Screenable candidate with relevant backend and project experience.",
  "strongest_signals": [
    "Backend API experience with Python, FastAPI, and PostgreSQL."
  ],
  "weak_or_confusing_signals": [
    "Impact is not quantified."
  ],
  "credibility_risks": [
    "Some project claims lack scale or user outcome evidence."
  ],
  "evidence_quotes": [
    {
      "quote": "Built backend API endpoints for a patient onboarding workflow using Python, FastAPI, and PostgreSQL.",
      "reason": "Shows relevant backend stack and product context."
    }
  ],
  "suggested_fixes": [
    "Add measurable outcomes for API work if accurate."
  ],
  "final_summary": "Good foundation, but stronger metrics and ownership details would improve confidence."
}
```

## Example Output

See `docs/example_ollama_output.md` for a fake sample resume output.

## How This Differs From Copy-Pasting Into ChatGPT

Copy-pasting into ChatGPT is better for one-off personal advice because it is fast and requires no local setup.

This layer is useful when the product needs:

- Repeatable persona-specific reviews.
- Local execution without paid APIs.
- Structured JSON outputs.
- Evidence quotes for every major judgment.
- Aggregation across evaluator types.
- Version comparison later.
