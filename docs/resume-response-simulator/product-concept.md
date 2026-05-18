# Product Concept

## Core Idea

The Resume Response Simulator predicts how different evaluators will perceive a resume or professional document before the user sends it.

The product flow:

```text
Resume/document upload
-> Parse text and layout
-> Extract structured candidate profile
-> Simulate reader personas
-> Evaluate first-pass reaction
-> Score confidence using evidence
-> Identify strong, weak, inflated, confusing, or missing signals
-> Suggest rewrites for target roles
-> Optionally compare multiple versions
```

## Reader-Response Simulator Framing

A resume is not just a data file. It is a stimulus shown to a reader under time pressure. The first-pass response often determines whether the document gets deeper attention.

The product treats the resume as something that creates different reactions depending on reader context:

| Reader | Typical Question |
| --- | --- |
| Technical recruiter | Is this person plausibly qualified and worth screening? |
| Engineering manager | Can this person do the work on my team? |
| AI/ML reviewer | Are the ML claims technically real? |
| Graduate admissions reviewer | Does this show research promise and academic fit? |
| Skeptical reviewer | What sounds inflated or unsupported? |
| ATS parser | Can structured systems extract the right fields? |
| Startup founder | Can this person move fast and own ambiguous work? |
| Non-technical HR reader | Is the story understandable and professional? |

## Why Normal Resume Checkers Are Weak

Normal resume checkers often do one of three things:

- Keyword matching against a job description.
- Generic formatting and grammar feedback.
- Broad LLM advice that sounds helpful but is not calibrated to a real evaluator.

Common weaknesses:

- They over-index on keywords.
- They do not simulate different reader types.
- They do not cite exact evidence for judgments.
- They rarely distinguish credible strength from inflated language.
- They cannot explain why one version creates a stronger first impression than another.
- They do not track disagreement between reviewers.
- They often produce advice that is reasonable but generic.

## Why Simulated Evaluator Response Is More Useful

A candidate does not only need to know whether a bullet is "good." They need to know how it lands.

Examples:

- A recruiter may like clear company names, scope, and skill keywords.
- An engineering manager may care more about ownership, tradeoffs, reliability, and production impact.
- An AI/ML reviewer may penalize vague claims like "used AI" without model details, data scale, metrics, or baselines.
- A skeptical reviewer may flag unsupported leadership, inflated impact, or suspiciously broad claims.
- An ATS parser may fail if dates, titles, or sections are formatted irregularly.

The system is useful when it explains:

- What each reader notices first.
- What each reader trusts.
- What each reader doubts.
- What evidence supports the reaction.
- How to rewrite the resume for a specific audience.

## Example Output

```json
{
  "overall_response": "Mixed",
  "first_impression": "Strong technical keywords, but impact claims are vague and several bullets read like task lists.",
  "persona": "software_engineering_manager",
  "strongest_signals": [
    {
      "signal": "Backend production experience",
      "evidence": "Built REST APIs in Node.js and PostgreSQL for customer onboarding workflow"
    }
  ],
  "weak_or_confusing_signals": [
    {
      "issue": "Impact is not quantified",
      "evidence": "Improved system performance and user experience"
    }
  ],
  "credibility_risks": [
    {
      "risk": "Generic AI wording",
      "evidence": "Implemented AI-powered solution for automation"
    }
  ],
  "role_fit_score": 68,
  "confidence": {
    "score": 0.74,
    "reason": "Most judgments are supported by cited lines, but the resume lacks enough project scale and outcome data."
  }
}
```

## Response Labels

| Label | Meaning |
| --- | --- |
| Great | Strong, credible, role-aligned, and clear under time pressure. |
| Good | Solid fit with fixable gaps or moderate specificity issues. |
| Mixed | Some strong signals, but the reader must work too hard or doubt key claims. |
| Weak | Missing important evidence, unclear role fit, or low signal density. |
| Bad | Confusing, unsupported, misaligned, or likely to be rejected quickly. |

