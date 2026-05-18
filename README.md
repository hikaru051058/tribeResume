# tribeResume

`tribeResume` is an experimental document perception-report system for resumes and professional documents.

The core workflow treats a resume as a timed text stimulus:

```text
document
-> parser
-> synthetic Word/Text/Sentence events
-> TRIBE v2 prediction or mock development signal
-> per-segment and section-level proxy features
-> cautious perception report
-> optional reviewer-agent comparison
```

This is not a resume checker and not an automatic resume editor. Real TRIBE output is still a proxy signal from synthetic reading events. No human is scanned, and the system does not predict hiring outcomes.

## Start Here

Use the main documentation:

- [docs/README.md](docs/README.md) for workflows and commands.
- [docs/tribe_core_architecture.md](docs/tribe_core_architecture.md) for the TRIBE-first architecture.
- [docs/perception_report_workflow.md](docs/perception_report_workflow.md) for the primary report flow.
- [docs/real_tribe_probe.md](docs/real_tribe_probe.md) for guarded real TRIBE prediction.
- [docs/real_tribe_output_interpretation.md](docs/real_tribe_output_interpretation.md) for how to read prediction and timeline outputs.
- [docs/demo_report.md](docs/demo_report.md) for a sanitized showcase report.

## Quick Mock Demo

Run the safe mock pipeline on the fake sample resume:

```bash
bash scripts/demo_mock.sh
```

This uses `examples/resume_sample.txt` and mock perception values. Mock mode is only for demonstrating the report workflow; it is not meaningful TRIBE output.

Show the bundled demo report:

```bash
bash scripts/show_demo_report.sh
```

## Real TRIBE Setup

Real TRIBE runs require local TRIBE dependencies and Hugging Face access to the configured text model dependency:

```bash
huggingface-cli login
python src/run_real_tribe_probe.py \
  --input examples/resume_sample.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --feature-device cpu \
  --event-format canonical \
  --output-prefix sample
```

Real runs can be slow and should be done intentionally. Use dry-run mode first:

```bash
python src/run_real_tribe_probe.py \
  --input examples/resume_sample.txt \
  --dry-run \
  --event-format canonical \
  --output-prefix sample
```

## Demo Report

The sanitized showcase report lives at [docs/demo_report.md](docs/demo_report.md). It summarizes:

- real TRIBE prediction shape and retained segments
- exact per-segment statistics
- section-level signal highlights
- a controlled dense-vs-clear wording variant
- limitations and next steps

## Visual Dashboard

Generate interactive Plotly.js dashboards from existing JSON outputs:

```bash
python src/generate_visual_report.py \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --features outputs/hikaru_real_position_tribe_perception_features.json \
  --variant-comparison outputs/variant_experiments/sem_variant/variant_comparison.json \
  --output-dir outputs/visualizations

open outputs/visualizations/index.html
```

These dashboards do not rerun TRIBE and do not require full prediction arrays.

Optional brain heatmap tooling requires a full `.npz` prediction array saved with `--save-full-array`:

```bash
python src/inspect_tribe_plotting.py
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --start-segment 0 \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_first_15.png
```

Notebook-like cortical panels should be generated as PNG/SVG/PDF. HTML vertex line graphs are fallback-only. If full arrays or plotting dependencies are missing, the brain visualizer writes diagnostics and falls back gracefully.

## Safety / Limitations

- No human was scanned.
- Synthetic reading events are not natural reading behavior.
- TRIBE output is a proxy signal, not measured perception.
- The system does not predict hiring outcomes.
- The system does not prove resume quality.
- Mock mode is for development/demo only.
- Generated outputs and local cache files should stay out of git.

## What This Project Proves

- Resume text can be converted into canonical TRIBE/neuralset events.
- A real TRIBE v2 checkpoint can run on synthetic resume-reading events.
- Prediction output can be summarized into per-segment statistics.
- Time segments can be mapped back to document sections.
- Section-level proxy reports and controlled variant comparisons are feasible.

## What This Project Does Not Prove

- It does not prove that TRIBE predicts recruiter behavior.
- It does not prove that lower load proxy means a better resume.
- It does not validate hiring, admissions, or interview outcomes.
- It does not replace human review.
- It does not yet model visual PDF layout or scanned/image PDFs.

## Privacy

Generated outputs, model caches, personal resume PDFs, notebooks, and local TRIBE checkouts are ignored by git. Keep real resumes and generated reports local unless you intentionally sanitize them.
