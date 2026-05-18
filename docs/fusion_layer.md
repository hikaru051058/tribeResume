# Fusion Layer

## Why Fusion Is Needed

TRIBE-style perception hypotheses and Ollama reviewer feedback answer different questions.

TRIBE-derived features may suggest that a section is salient, dense, or underemphasized as a document stimulus. Reviewer agents may identify semantic concerns such as missing AI/ML specificity, unclear ownership, or weak evidence.

Fusion combines these signals so the report can prioritize sections that are both cognitively important and semantically important.

## Agreement

Agreement means the perception hypothesis and reviewer critique point toward the same section or issue.

Example:

- Perception signal: projects may feel dense.
- Reviewer signal: AI/ML reviewer says projects lack model/data/evaluation specificity.
- Fusion target: suggest inspecting project bullets for technical evidence and AI/ML clarity.

## Disagreement

Disagreement means one layer flags an issue that the other does not.

Example:

- Perception signal: skills section may be underemphasized.
- Reviewer signal: no reviewer concern about skills.
- Interpretation: inspect manually before patching; it may be a formatting/perception issue rather than a semantic weakness.

## Mock Vs Real TRIBE Output

Mock perception data is development-only. It is marked:

```json
{
  "mock": true,
  "not_real_tribe_output": true
}
```

When perception source is mock, fusion reports must say the signal is not real TRIBE output.

Real TRIBE output would still be experimental. It should not be described as actual perception, real brain measurement, or hiring prediction.

## Confidence Separation

Fusion reports use three separate confidence values:

- `text_review_confidence`: confidence from the reviewer-agent summary, usually the average confidence reported by the Ollama reviewer layer. This means the language-review agents were relatively internally consistent or evidence-backed. It does not mean the system knows the true hiring outcome.
- `perception_signal_confidence`: confidence in the TRIBE-style perception signal. When `--mock` is used, this is intentionally low and capped at 0.30 because the signal is not real TRIBE output.
- `fusion_confidence`: confidence that reviewer feedback and perception hypotheses point toward the same improvement targets. This is based on agreement strength between the two sources, not on resume quality itself.

These values should not be collapsed into one objective score. A review can have moderate text confidence while perception confidence remains low because the perception input is mock-only.

Mock perception should never be treated as neuroscience output, real brain activity, or measured recruiter perception.

## How Fusion Guides Suggestions

Fusion produces prioritized suggestions, not automatic edits. A fusion target should tell the user what to inspect and why.

Example:

- Section: Projects.
- Perception signal: dense/cognitive-load proxy.
- Reviewer signal: missing model/data/evaluation specificity.
- Suggestion: inspect project bullets for whether strong AI/ML evidence is buried or missing.

## Optional Patch Mode

Patch mode can accept a fusion report:

```bash
python src/run_bullet_patch.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --fusion-report outputs/fusion_report.json
```

The patch prompt receives the top three prioritized fusion targets and should focus suggestions there. This is optional and downstream of the perception report.

## Example

```text
Perception hypothesis:
Experience may draw attention and feel dense.

Reviewer critique:
AI/ML reviewer wants more model/data/evaluation specificity.

Suggestion priority:
Inspect the SEM Medical Solutions bullets for whether workload metrics, AI-system architecture, and evaluation context are clear without adding unsupported details.
```
