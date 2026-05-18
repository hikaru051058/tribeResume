# Perception Report Workflow

## Main Product Flow

The main workflow is a document perception report, not automatic resume editing.

```text
Document
-> parser
-> artificial reading events
-> TRIBE v2 prediction or mock prediction
-> feature extraction
-> perception hypotheses
-> Ollama interpretation
-> suggestion report
```

## Step 1: Run The Perception Probe

Use mock mode only for development and demo work:

```bash
python src/run_tribe_perception_probe.py \
  --input path/to/resume.pdf \
  --mock
```

This writes:

- `outputs/tribe_events.json`
- `outputs/mock_tribe_prediction.json`
- `outputs/tribe_perception_features.json`
- `outputs/tribe_perception_hypotheses.json`

Mock output is not real TRIBE output. It exists so the downstream feature, interpretation, UI, and report layers can be built before or without running the full model path.

Mock mode should not be used for real perception conclusions. A mock report can demonstrate the product workflow, but its proxy values are synthetic and should not be interpreted as document perception signals.

## Real TRIBE Output Mode

Real TRIBE mode is required for serious experimental perception reports. After running a real TRIBE probe, convert the saved prediction summary into perception features:

```bash
python src/run_real_tribe_probe.py \
  --input examples/resume_sample.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --feature-device cpu \
  --event-format canonical \
  --output-prefix sample \
  --verbose-errors

python src/run_tribe_timeline_analysis.py \
  --input examples/resume_sample.txt \
  --prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --segment-stats outputs/sample_real_tribe_segment_stats.json \
  --events outputs/sample_real_tribe_events_canonical.csv \
  --output outputs/sample_tribe_timeline_analysis.json

python src/run_tribe_perception_probe.py \
  --input examples/resume_sample.txt \
  --real-prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --timeline-analysis outputs/sample_tribe_timeline_analysis.json \
  --output-prefix sample_real
```

This creates real-source feature files:

- `outputs/sample_real_tribe_perception_features.json`
- `outputs/sample_real_tribe_perception_hypotheses.json`

The source is marked `real_tribe`, with this caution:

```text
Real TRIBE checkpoint output on synthetic resume-reading events; not measured brain activity.
```

The real-source mode still estimates perception proxies, not hiring outcomes or resume quality. It is experimental because the resume is represented as synthetic reading events rather than natural reading behavior or measured human response data.

## Step 2: Inspect Raw TRIBE Or Mock Output

The raw real TRIBE prediction is the stimulus-response-style signal. It should be treated as an experimental proxy.

Mock output is only a development stand-in for this signal. It should be clearly marked as demo mode and should not be used as a substitute for real TRIBE output.

The output may support hypotheses about:

- response intensity
- section salience
- cognitive-load proxy
- dense or confusing sections
- underemphasized sections

The main report should expose the actual proxy values per section instead of hiding them behind prose:

- `salience_proxy`
- `position_normalized_salience`
- `cognitive_load_proxy`
- `underemphasis_proxy`
- `response_intensity`

It does not prove actual brain activity, actual reader perception, hiring outcomes, or resume quality.

## Step 3: Interpret Features

Generate a human-readable perception report:

```bash
python src/run_perception_interpretation.py \
  --input path/to/resume.pdf \
  --features outputs/tribe_perception_hypotheses.json \
  --model qwen3:14b \
  --target-role "AI backend engineer intern"
```

This writes:

- `outputs/perception_interpretation.json`
- `outputs/perception_interpretation.md`

Ollama interprets TRIBE-derived perception hypotheses and resume text. It should explain what the signals may suggest and what cannot be concluded.

The report should cover all major sections that appear in the perception feature file, such as intro/contact, education, experience, projects, publications, and skills. Each section should include short evidence phrases from the resume text so the user can see what the signal is attached to.

The Markdown report also includes proxy ranking tables:

- Highest salience.
- Highest cognitive-load proxy.
- Most underemphasized.

These tables make it easier to see which sections should be inspected first.

## Step 4: Produce Suggestions

The report should produce suggestion priorities, not automatic edits.

Each suggestion priority should show the source signals behind it:

- salience proxy
- cognitive-load proxy
- underemphasis proxy
- evidence phrases used
- reasoning tied to the target role

Good suggestions sound like:

- "Inspect whether the projects section is too dense for a first-pass reader."
- "Consider surfacing model/data/evaluation context if the target role is AI-heavy."
- "Check whether strong evidence is buried in a low-salience section."

The user decides whether to edit the document.

Suggestion priorities are inspection priorities. They are not guaranteed fixes and should not be described as improving hiring outcomes.

## Optional Reviewer Comparison

Reviewer agents can be run for comparison:

```bash
python src/run_ollama_review.py \
  --profile balanced \
  --input path/to/resume.pdf \
  --output-prefix review
```

Then fuse reviewer feedback with perception hypotheses:

```bash
python src/run_fusion.py \
  --input path/to/resume.pdf \
  --perception outputs/tribe_perception_hypotheses.json \
  --review-summary outputs/review_ollama_review_summary.json \
  --output outputs/fusion_report.json
```

Fusion produces prioritized suggestions. It should not be treated as an automatic editing step.

## Shortcut

Run the primary report pipeline:

```bash
python src/run_full_perception_report.py \
  --input path/to/resume.pdf \
  --target-role "AI backend engineer intern" \
  --model qwen3:14b \
  --mock
```

Add optional reviewer comparison:

```bash
python src/run_full_perception_report.py \
  --input path/to/resume.pdf \
  --target-role "AI backend engineer intern" \
  --model qwen3:14b \
  --mock \
  --with-review \
  --review-profile balanced
```

## Limits

- Mock output is not real TRIBE output.
- Mock reports are pipeline demos, not real TRIBE interpretations.
- Mock reports should not be used for real perception conclusions.
- Serious experimental reports should use real TRIBE output when available.
- Real TRIBE output is still a proxy signal.
- Real TRIBE reports are still experimental because the input is a synthetic reading timeline.
- The system estimates possible document perception, not outcomes.
- Suggestions are not automatic edits.
- Reviewer-agent feedback is optional comparison, not the core product by itself.
