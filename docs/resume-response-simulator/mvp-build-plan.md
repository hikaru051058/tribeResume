# MVP Build Plan

## Guiding Principle

This document was written before the TRIBE-first refactor. The current implementation starts with the perception-report workflow:

```text
parser -> synthetic reading events -> TRIBE/mock prediction -> feature extraction -> perception report
```

Persona simulation, rewriting, patching, and comparison are now optional downstream tools.

## Phase 0: Docs And Examples

Priority: High  
Difficulty: Low

Deliverables:

- Product concept documentation.
- Example inputs and outputs.
- Persona definitions.
- JSON schemas.
- Evaluation plan.
- Risk and limitation documentation.

Success criteria:

- A developer can understand the system without additional explanation.
- A designer can sketch the product flow.
- A future implementation can use the documented schemas.

## Phase 1: Parser And Perception Events

Priority: Highest  
Difficulty: Medium

Deliverables:

- PDF/DOCX/text parsing.
- Markdown parsing.
- Bounded section extraction.
- Synthetic word events.
- Canonical TRIBE/neuralset DataFrame events.
- Dry-run diagnostics.

Recommended stack:

- Document parser.
- Event generator.
- TRIBE probe wrapper.
- JSON schema validation.
- Local output directory with ignored generated artifacts.

## Phase 2: Real TRIBE Output Inspection

Priority: High  
Difficulty: Medium

Deliverables:

- Guarded real TRIBE prediction script.
- Output serializer with compact per-segment stats.
- Segment summary and diagnostics.
- Timeline analysis mapped to document sections.
- Position-normalized salience heuristic.
- Markdown timeline report.

Success criteria:

- Real TRIBE can run on sample synthetic text events.
- The report clearly states no human scan and no hiring prediction.
- Section-level aggregation is inspectable and reproducible.

## Phase 3: Perception Report And Interpretation

Priority: Medium
Difficulty: Medium

Deliverables:

- Perception interpretation JSON.
- Markdown perception report.
- Proxy ranking tables.
- Evidence phrases per section.
- Deterministic signal insights.
- Mock-vs-real source warnings.

## Phase 4: Optional Comparison And Editing

Priority: Medium  
Difficulty: Medium

Deliverables:

- Ollama reviewer-agent comparison.
- Perception-review fusion.
- Bullet patch suggestions.
- Evidence scope validation.
- Controlled variant experiments.

Success criteria:

- Optional tools never override the core report.
- Patch/rewrite output preserves factual evidence.
- Variant comparison warns about short-section and segment-boundary instability.

Success criteria:

- User can see whether a rewrite actually improves the simulated response.
- The system explains why a version wins.

## Phase 4: Optional TRIBE v2 Experiment

Priority: Low until core product works  
Difficulty: High

Deliverables:

- Render resume pages into visual/text stimuli.
- Compute baseline layout metrics.
- Prototype stimulus-response or attention analysis.
- Compare outputs against cheaper deterministic density metrics.
- Decide whether TRIBE v2 adds measurable value.

Success criteria:

- The experiment improves prediction of human readability or attention outcomes beyond simple layout metrics.
- Results are labeled experimental and do not drive semantic judgment.

## What Not To Build First

Avoid building these before the core reader-response loop works:

- TRIBE v2 production integration.
- Complex brain visualization.
- Fine-tuned hiring model.
- Automated application submission.
- A marketplace of resume templates.
- Large dashboard analytics.
- Overly precise numerical scoring without calibration.
- Claims that the system predicts hiring outcomes.

## Recommended Implementation Order

1. Parser and line-numbered evidence extraction.
2. Structured candidate profile schema.
3. One or two high-value personas: recruiter and engineering manager.
4. Evidence-cited JSON output validation.
5. Confidence scoring.
6. Rewrite suggestions.
7. Job-description matching.
8. Version comparison.
9. Additional personas.
10. Optional TRIBE v2 experiment.
