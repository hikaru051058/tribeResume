# Tribe Resume Documentation

## Current Product Framing

This repository is an experimental document perception-report system. The core idea is to treat a resume or professional document as a stimulus, estimate section-level perception proxy signals, and turn those signals into cautious suggestions.

The current implementation supports two perception paths:

- `real_tribe`: real TRIBE v2 checkpoint output from synthetic resume-reading events.
- `mock`: deterministic development values for testing the report pipeline only.

Mock mode is not a meaningful perception signal. It exists for UI, report, and workflow development. Serious experimental reports should use real TRIBE output when available.

## Core System Philosophy

TRIBE v2 is the core experimental perception layer. The product is not primarily an Ollama resume checker.

The intended flow is:

```text
resume/document stimulus
-> TRIBE-style predicted response pattern
-> perception proxy features
-> cautious perception hypotheses
-> Ollama interpretation and explanation
-> suggestion report
```

Ollama is not the core judge. Ollama interprets TRIBE-derived signals and resume text evidence, then explains what those signals may suggest. Suggestions are inspection priorities, not automatic edits.

TRIBE v2 does not prove real recruiter decisions or directly judge resume quality. Its output should be treated as an experimental proxy signal.

## Current Local Implementation

The current pipeline can:

- Parse TXT, Markdown, DOCX, and text-based PDF resumes.
- Convert resume text into canonical TRIBE/neuralset `Word`, `Text`, and `Sentence` events.
- Run dry-run event inspection without loading TRIBE.
- Run real TRIBE v2 prediction when local Hugging Face access and dependencies are available.
- Save compact exact per-segment prediction statistics without committing giant arrays.
- Map retained TRIBE time segments back to resume sections.
- Generate proxy rankings for salience, position-normalized salience, cognitive-load proxy, and underemphasis proxy.
- Generate a human-readable perception report with evidence phrases and deterministic signal insights.
- Optionally compare perception hypotheses with Ollama reviewer-agent feedback.
- Optionally run controlled variant experiments to test whether proxy signals change when wording changes while facts are preserved.

The local notebook and TRIBE checkout are not part of the committed app workflow.

## Real TRIBE Probe

Use dry run first to verify parsing and synthetic reading events without loading TRIBE:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run
```

Inspect the raw canonical DataFrame path:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run \
  --event-format dataframe
```

Try the canonical TRIBE transform path without prediction:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run \
  --event-format canonical
```

Attempt a guarded real TRIBE call only when explicitly testing model prediction:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix sample
```

The real probe saves raw output or structural diagnostics. It does not interpret the result as resume quality, actual perception, or a hiring prediction.

## Real TRIBE Output Inspection Workflow

Run the real probe to generate canonical events and raw prediction summary:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix sample
```

With `--output-prefix sample`, the probe writes:

- `outputs/sample_real_tribe_prediction_raw.json`
- `outputs/sample_real_tribe_segment_stats.json`
- `outputs/sample_real_tribe_segments_summary.json`
- `outputs/sample_real_tribe_events.json`
- `outputs/sample_real_tribe_events_dataframe.csv`
- `outputs/sample_real_tribe_events_canonical.csv`
- `outputs/sample_real_tribe_probe_diagnostics.json`

Analyze the retained TRIBE time segments and map them back to resume sections:

```bash
python src/run_tribe_timeline_analysis.py \
  --input path/to/resume.pdf \
  --prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --segment-stats outputs/sample_real_tribe_segment_stats.json \
  --events outputs/sample_real_tribe_events_canonical.csv \
  --output outputs/sample_tribe_timeline_analysis.json
```

Optionally save the full prediction array as compressed `.npz`:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix sample \
  --save-full-array
```

Convert real TRIBE output plus timeline analysis into perception features:

```bash
python src/run_tribe_perception_probe.py \
  --input path/to/resume.pdf \
  --real-prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --timeline-analysis outputs/sample_tribe_timeline_analysis.json \
  --output-prefix real_resume
```

Generate the human-readable perception report:

```bash
python src/run_perception_interpretation.py \
  --input path/to/resume.pdf \
  --features outputs/real_resume_tribe_perception_hypotheses.json \
  --model qwen3:14b \
  --target-role "AI backend engineer intern"
```

The perception report includes deterministic signal insights generated directly from proxy rankings. These reduce overreliance on LLM phrasing by always surfacing:

- the highest-salience section
- the highest cognitive-load-proxy section
- the highest underemphasis-proxy section
- the evidence phrases attached to those rankings

The timeline report shows raw prediction shape, retained segments, output dimensions, segment timing, section mapping, and section-level response proxies. These are inspection signals, not resume-quality scores.

## Visualization Workflow

Generate interactive Plotly visualizations from existing JSON outputs:

```bash
python src/generate_visual_report.py \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --features outputs/hikaru_real_position_tribe_perception_features.json \
  --variant-comparison outputs/variant_experiments/sem_variant/variant_comparison.json \
  --output-dir outputs/visualizations

open outputs/visualizations/index.html
```

This creates:

- `outputs/visualizations/hikaru_timeline.html`
- `outputs/visualizations/hikaru_section_signals.html`
- `outputs/visualizations/sem_variant_comparison.html`
- `outputs/visualizations/index.html`

These visualizations use saved timeline, feature, and variant JSON files. They do not rerun TRIBE and do not need full prediction arrays.

Optional brain heatmap inspection:

```bash
python src/inspect_tribe_plotting.py

python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --start-segment 0 \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_first_15.png
```

Meta-style section window:

```bash
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_experience_peak.png
```

Stimulus-label version, if segment objects were saved:

```bash
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --segments-pkl outputs/hikaru_real_tribe_segments.pkl \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --start-segment 0 \
  --n-timesteps 15 \
  --show-stimuli \
  --output outputs/visualizations/brain_first_15.png
```

Brain heatmaps require full prediction arrays saved with `--save-full-array`. Stimulus labels work best when segment objects are saved with `--save-segment-objects`. If the `.npz`, segment objects, or plotting dependencies are missing, the visualizer falls back to diagnostics or a vertex-value view. HTML vertex line graphs are fallback-only; notebook-like cortical panels should be generated as PNG/SVG/PDF with `render_brain_timesteps_panel.py`.

Interactive timestep slider:

```bash
python src/render_brain_activity_slider.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --events outputs/hikaru_real_tribe_events_canonical.csv \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_activity_slider.html

open outputs/visualizations/brain_activity_slider.html
```

Six-angle slider:

```bash
python src/render_brain_activity_slider.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --events outputs/hikaru_real_tribe_events_canonical.csv \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --view-preset six \
  --output outputs/visualizations/brain_activity_slider_6view.html

open outputs/visualizations/brain_activity_slider_6view.html
```

Pseudo-3D viewer from the six-view frames:

```bash
python src/build_brain_3d_viewer.py \
  --slider-diagnostics outputs/visualizations/brain_activity_slider_6view_diagnostics.json \
  --output outputs/visualizations/brain_3d_viewer.html

open outputs/visualizations/brain_3d_viewer.html
```

Actual browser 3D cortical mesh viewer:

```bash
python src/build_brain_mesh_viewer.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --events outputs/hikaru_real_tribe_events_canonical.csv \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --value-mode absolute \
  --colorscale activity \
  --output outputs/visualizations/brain_mesh_3d_viewer.html

open outputs/visualizations/brain_mesh_3d_viewer.html
```

Do not commit generated visualization artifacts, full arrays, raw predictions, or segment stats:

- `outputs/*.npz`
- `outputs/*prediction_full*.npz`
- `outputs/*segments.pkl`
- `outputs/*real_tribe_prediction_raw.json`
- `outputs/*real_tribe_segment_stats.json`

## Controlled Variant Experiment Workflow

Use controlled variants to test whether real TRIBE-derived proxy signals change when wording changes while facts are preserved.

Dry run first. This prints the planned commands and does not call TRIBE:

```bash
python src/run_variant_experiment.py \
  --variant-a examples/variant_experiments/dense_sem_bullet.txt \
  --variant-b examples/variant_experiments/clear_sem_bullet.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --target-role "AI backend engineer intern" \
  --output-prefix sem_variant \
  --dry-run
```

Run the full experiment only when ready. This calls real TRIBE twice:

```bash
python src/run_variant_experiment.py \
  --variant-a examples/variant_experiments/dense_sem_bullet.txt \
  --variant-b examples/variant_experiments/clear_sem_bullet.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --target-role "AI backend engineer intern" \
  --output-prefix sem_variant
```

Compare the generated signals:

```bash
python src/compare_variant_signals.py \
  --a-features outputs/variant_experiments/sem_variant/sem_variant_a_tribe_perception_features.json \
  --b-features outputs/variant_experiments/sem_variant/sem_variant_b_tribe_perception_features.json \
  --output outputs/variant_experiments/sem_variant/variant_comparison.json
```

This experiment does not validate hiring outcomes. It only checks whether the TRIBE-derived proxy pipeline changes under a controlled wording change.

Generate a final demo summary from existing outputs:

```bash
python src/generate_demo_report.py \
  --full-report outputs/hikaru_real_position_perception_interpretation.md \
  --timeline-report outputs/hikaru_tribe_timeline_analysis.md \
  --variant-report outputs/variant_experiments/sem_variant/variant_comparison.md \
  --output outputs/demo_report.md
```

## Primary Workflow: Perception Report

For a development/demo report, run a mock perception probe:

```bash
python src/run_tribe_perception_probe.py \
  --input path/to/resume.pdf \
  --mock
```

Mock mode is only for testing the report pipeline. It should not be used to interpret a real document.

For a serious experimental report, first run the real TRIBE probe and timeline analysis from the sections above, then convert those real outputs into perception features:

```bash
python src/run_tribe_perception_probe.py \
  --input path/to/resume.pdf \
  --real-prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --timeline-analysis outputs/sample_tribe_timeline_analysis.json \
  --output-prefix real_resume
```

Interpret the perception hypotheses and produce a suggestion report:

```bash
python src/run_perception_interpretation.py \
  --input path/to/resume.pdf \
  --features outputs/real_resume_tribe_perception_hypotheses.json \
  --model qwen3:14b \
  --target-role "AI backend engineer intern"
```

This writes:

- `outputs/perception_interpretation.json`
- `outputs/perception_interpretation.md`

The report shows what the TRIBE-style output may suggest about salience, density, confusion, underemphasis, and reader-perception hypotheses. It does not rewrite the resume.

Shortcut:

```bash
python src/run_full_perception_report.py \
  --input path/to/resume.pdf \
  --target-role "AI backend engineer intern" \
  --model qwen3:14b \
  --mock
```

When using `--mock`, perception confidence is intentionally low because the signal is not real TRIBE output.

Optional reviewer comparison:

```bash
python src/run_ollama_review.py \
  --profile balanced \
  --input path/to/resume.pdf \
  --output-prefix review

python src/run_fusion.py \
  --input path/to/resume.pdf \
  --perception outputs/tribe_perception_hypotheses.json \
  --review-summary outputs/review_ollama_review_summary.json \
  --output outputs/fusion_report.json
```

## Supported Resume Formats

The local parser supports:

- TXT.
- Markdown.
- DOCX.
- Text-based PDF.

Scanned PDFs and image-only PDFs are not supported yet. Those need OCR in a later version. If a PDF has little or no extractable text, the parser warns that it may be scanned or image-based.

DOCX tables are parsed, but layout may not be preserved. PDF visual layout is also not fully understood yet, especially for multi-column resumes or heavily designed documents.

## Optional Reviewer-Agent Comparison

Ollama is the local LLM layer for evaluator simulation. It is used to simulate semantic reader reactions from personas such as technical recruiter, software engineering manager, AI/ML reviewer, graduate admissions reviewer, skeptical reviewer, and ATS parser.

Ollama reviewer agents are optional comparison tools. They are not the core product by themselves. The core workflow starts from TRIBE-style perception signals and produces a document perception report.

The MVP can run for free locally on an M1 Max 64GB MacBook Pro. No paid API is required, and the scaffold does not use OpenAI or Claude APIs.

Recommended local models:

- `llama3.1:8b` for fast testing.
- `qwen3:14b` for deeper engineering, AI/ML, and skeptical critique.

Setup commands:

```bash
brew install ollama
ollama serve
ollama pull qwen3:14b
ollama pull llama3.1:8b
```

Run reviewer agents:

```bash
python src/run_ollama_review.py --profile fast
python src/run_ollama_review.py --profile balanced
python src/run_ollama_review.py --profile deep
python src/run_ollama_review.py --profile adaptive --target-role "AI backend engineer intern"
python src/run_ollama_review.py --model llama3.1:8b
python src/run_ollama_review.py --model qwen3:14b
```

Profiles are defined in `configs/model_routing.yaml`. The manual `--model` argument overrides profile routing and runs every persona with the same model.

Profile guidance:

- `fast`: use while editing prompts, schemas, and UI.
- `balanced`: default profile; uses `llama3.1:8b` for faster screeners and `qwen3:14b` for deeper critique agents.
- `deep`: use when review quality matters more than runtime; runs all reviewers on `qwen3:14b`.
- `adaptive`: starts with `llama3.1:8b` and escalates selected agents to `qwen3:14b` when the first pass looks weak, generic, unsupported, or role-sensitive.

Selected agents:

```bash
python src/run_ollama_review.py --profile balanced --agents skeptical_reviewer,engineering_manager
```

Parallel mode:

```bash
python src/run_ollama_review.py --profile balanced --parallel
```

Parallel mode may increase memory pressure.

The reviewer output is simulated evaluator feedback. It does not predict real hiring outcomes.

## Optional Experimental Editing Tools

The following tools are downstream experiments. They should not be treated as the main workflow.

### Evidence-Preserving Rewrite

Rewrite defaults to surgical mode. It should preserve concrete evidence such as metrics, dates, company names, project names, role titles, technical stacks, publication names, and GPA unless you explicitly allow removal.

```bash
python src/run_resume_rewrite.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --mode surgical
```

Full mode allows broader restructuring, but still cannot invent facts and must report removed evidence:

```bash
python src/run_resume_rewrite.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --mode full \
  --allow-remove-gpa
```

### Targeted Bullet Patch Mode

For strong technical resumes, prefer bullet patches over full rewrites:

```bash
python src/run_bullet_patch.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --focus "AI/ML specificity"
```

Patch mode suggests one-bullet-at-a-time edits and keeps the original resume as the source of truth.

## Perception + Review Fusion Workflow

Fusion is optional. It compares perception hypotheses with reviewer-agent feedback and produces prioritized suggestions:

```bash
python src/run_fusion.py \
  --input path/to/resume.pdf \
  --perception outputs/tribe_perception_hypotheses.json \
  --review-summary outputs/review_ollama_review_summary.json \
  --output outputs/fusion_report.json
```

Fusion reports separate text-review confidence, perception-signal confidence, and fusion confidence. When using `--mock`, perception confidence is intentionally low because the signal is not real TRIBE output.

Use fusion targets to guide bullet patches:

```bash
python src/run_bullet_patch.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --fusion-report outputs/fusion_report.json
```
