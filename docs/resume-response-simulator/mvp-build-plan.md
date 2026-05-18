# MVP Build Plan

## Guiding Principle

Build the semantic reader-response system first. Do not start with TRIBE v2, brain-response modeling, or complex visual experiments. The product must first prove that structured persona simulation is better than a generic resume critique.

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

## Phase 1: Resume Parser And LLM Agents

Priority: Highest  
Difficulty: Medium

Deliverables:

- Resume upload endpoint.
- PDF/DOCX/text parsing.
- Line-numbered text extraction.
- Structured candidate profile extraction.
- Persona agent prompts.
- Evidence-cited JSON outputs.
- Basic report UI or API response.

Recommended stack:

- Backend API.
- Document parser.
- LLM orchestration layer.
- JSON schema validation.
- Storage for resume and analysis records.

## Phase 2: Job-Description Matching

Priority: High  
Difficulty: Medium

Deliverables:

- Job description upload or paste.
- Target role extraction.
- Role-fit rubric.
- Gap analysis.
- Targeted rewrite suggestions.
- Persona weighting by role.

Success criteria:

- Same resume can receive different role-fit results for different jobs.
- Recommendations cite both resume evidence and job requirement evidence.

## Phase 3: Version Comparison

Priority: Medium  
Difficulty: Medium

Deliverables:

- Compare two or more resume versions.
- Show winner by persona.
- Show tradeoffs.
- Track score changes.
- Recommend hybrid edits.

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

