# Product Direction

## Bigger Product Idea

The product is a document perception simulator for resumes and professional documents.

Core promise:

> Estimate how a document may land cognitively and semantically before sending it.

Target flow:

```text
Resume upload
-> Structured parsing
-> TRIBE-inspired response prediction
-> Response feature extraction
-> Perception hypotheses
-> LLM explanation
-> Evidence-preserving patching
```

## Structured Parsing

The system should parse:

- Contact information.
- Education.
- Experience.
- Projects.
- Skills.
- Dates.
- Claims.
- Metrics.
- Technologies.
- Missing or ambiguous fields.

Parsing should create an evidence index so every later judgment can cite exact resume lines.

## TRIBE-Inspired Response Prediction

TRIBE v2 is the core experimental perception layer. It can be used to produce predicted response patterns from resume/document stimuli.

The system should treat these outputs as proxy signals, not proof of actual perception.

Useful derived features:

- Section salience.
- Response intensity.
- Cognitive-load proxy.
- Underemphasized sections.
- Dense or confusing sections.

## LLM Explanation Layer

LLM agents explain and operationalize TRIBE-derived signals. They can also simulate reviewer personas as a baseline or comparison:

- Technical recruiter.
- Software engineering manager.
- AI/ML reviewer.
- Graduate admissions reviewer.
- Skeptical reviewer.
- ATS parser.
- Startup founder or technical cofounder.
- General non-technical HR reader.

Ollama alone is not the unique product. It is the explanation layer that turns experimental signals plus resume text into understandable hypotheses and patch priorities.

## Confidence Scoring

Confidence should be evidence-based, not just an LLM's self-reported certainty.

Useful confidence components:

- Parser confidence.
- Evidence coverage.
- Rubric consistency.
- Persona agreement.
- Missing required fields.
- Ambiguity penalties.
- Unsupported claim penalties.

## Evidence-Preserving Patching

Patch tools should improve the document while preserving concrete proof. For strong technical resumes, targeted bullet patches are safer than full rewrites.

## Why ChatGPT Is Better For One-Off Use

For a single personal resume review, copy-pasting into ChatGPT or Claude is often faster and more practical. It gives immediate advice without building a pipeline.

This product only becomes valuable if it adds structure that a one-off prompt does not provide:

- Repeatable multi-persona reviews.
- Evidence-cited findings.
- Version comparison.
- Role-specific scoring.
- Confidence breakdowns.
- Disagreement analysis between reviewer types.
- Stored history across resume iterations.

## Why A Structured Multi-Reviewer Simulator May Still Be Valuable

A structured simulator helps when users need to understand how the same resume lands differently:

- A recruiter may see a screenable candidate.
- An engineering manager may see weak ownership evidence.
- An ATS parser may extract the right skills.
- A skeptical reviewer may flag unsupported claims.
- A startup founder may value broader project ownership.

The product should preserve those differences instead of flattening them into one generic score.
