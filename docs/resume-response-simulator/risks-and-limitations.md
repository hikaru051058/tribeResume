# Risks And Limitations

## Overclaiming

Risk:

The product may imply it can predict hiring or admissions outcomes.

Mitigation:

- Describe outputs as simulated reader reactions, not outcome predictions.
- Avoid language like "guaranteed interview" or "acceptance probability."
- Calibrate labels against reviewer behavior where possible.

## Fake Objectivity

Risk:

Numerical scores can feel more objective than they are.

Mitigation:

- Show confidence breakdowns.
- Cite exact evidence.
- Preserve persona disagreement.
- Explain uncertainty and missing information.

## Bias

Risk:

LLM agents and rubrics may reproduce biased hiring assumptions.

Mitigation:

- Audit outputs for protected-class proxies.
- Avoid judging personal background unrelated to role criteria.
- Use explicit rubrics.
- Allow users to inspect and challenge reasoning.
- Test with diverse resumes and reviewers.

## Resume Outcome Uncertainty

Risk:

Even a strong resume can fail because of market conditions, timing, referrals, internal candidates, or reviewer preferences.

Mitigation:

- State that the system evaluates document response, not real-world certainty.
- Encourage role-specific iteration rather than universal scoring.

## LLM Hallucination

Risk:

The system may invent achievements, infer facts not present, or produce unsupported rewrites.

Mitigation:

- Require line citations.
- Validate JSON outputs.
- Mark rewrites that require user verification.
- Penalize unsupported claims in confidence scoring.
- Separate "from resume evidence" from "suggested if true."

## TRIBE V2 Mismatch

Risk:

TRIBE v2 could be misrepresented as a resume judgment model.

Mitigation:

- Label it as core but experimental perception-simulation infrastructure.
- Use it only for stimulus-response-like proxy signals, salience, density, or cognitive-load hypotheses.
- Do not use it to produce hiring/admissions labels.
- Compare it against simpler layout metrics before adding complexity.
- Always state that real TRIBE output comes from synthetic reading events and that no human was scanned.
- Keep mock mode clearly labeled as development/demo-only.

## Privacy Concerns

Risk:

Resumes contain personal data, employment history, education, contact information, and sometimes sensitive details.

Mitigation:

- Minimize data retention.
- Encrypt files at rest and in transit.
- Provide deletion controls.
- Avoid training on user resumes without explicit consent.
- Redact contact information from logs.
- Limit access to analysis records.

## Misleading Rewrites

Risk:

Suggested rewrites may make the candidate sound more accomplished than the evidence supports.

Mitigation:

- Avoid adding metrics unless provided by the user.
- Label assumptions.
- Ask for missing facts before generating high-specificity rewrites.
- Provide conservative rewrites when evidence is thin.

## ATS Over-Optimization

Risk:

Users may stuff keywords or optimize for parsers at the expense of human credibility.

Mitigation:

- Separate ATS parser feedback from human persona feedback.
- Warn when keyword density creates credibility or readability issues.
- Balance role-fit scoring with evidence and clarity.
