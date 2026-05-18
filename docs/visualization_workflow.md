# Visualization Workflow

## Purpose

The visualization layer makes existing TRIBE resume perception outputs easier to inspect without rerunning TRIBE. Phase 1 uses Plotly dashboards from compact JSON summaries. Phase 2 optionally renders brain-surface-style heatmaps if a full prediction array was saved.

Every visualization should carry this caution:

- Real TRIBE output from synthetic resume-reading events.
- No human was scanned.
- This is not a hiring prediction.
- Section-level aggregation is a proxy.

## Timeline Visualization

```bash
python src/visualize_timeline.py \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --output outputs/visualizations/hikaru_timeline.html
```

This shows segment-level `response_abs_mean` and `response_std` over synthetic reading time, colored by mapped section.

Use it to inspect:

- whether response intensity clusters by section
- whether high variance/load spans are concentrated
- whether segment mapping looks plausible
- whether exact per-segment stats or approximations were used

## Section Signal Dashboard

```bash
python src/visualize_section_signals.py \
  --features outputs/hikaru_real_position_tribe_perception_features.json \
  --output outputs/visualizations/hikaru_section_signals.html
```

This shows section-level bars for:

- `response_intensity`
- `salience_proxy`
- `position_normalized_salience`
- `cognitive_load_proxy`
- `underemphasis_proxy`

Use it to compare sections, not to assign objective quality scores.

## Variant Comparison Visualization

```bash
python src/visualize_variant_comparison.py \
  --comparison outputs/variant_experiments/sem_variant/variant_comparison.json \
  --output outputs/visualizations/sem_variant_comparison.html
```

This compares controlled variants that preserve the same facts while changing wording. It shows:

- Variant A vs B cognitive-load proxy
- Variant A vs B normalized salience
- delta load by section
- delta normalized salience by section
- facts-preserved status
- stability warnings

Short sections and shifted segment boundaries can create unstable changes. Treat the result as an inspection cue.

## Full Visual Report

```bash
python src/generate_visual_report.py \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --features outputs/hikaru_real_position_tribe_perception_features.json \
  --variant-comparison outputs/variant_experiments/sem_variant/variant_comparison.json \
  --output-dir outputs/visualizations
```

Open:

```bash
open outputs/visualizations/index.html
```

The index links to all generated Plotly dashboards and summarizes limitations.

## Optional Brain Heatmaps

Brain heatmaps require a full prediction array saved with `--save-full-array`:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix hikaru \
  --save-full-array
```

Inspect available TRIBE plotting helpers:

```bash
python src/inspect_tribe_plotting.py
```

Render a notebook-like Meta-style timestep panel:

```bash
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_experience_peak.png
```

Pass `--segments-pkl outputs/hikaru_real_tribe_segments.pkl --show-stimuli` when full segment objects are available. HTML vertex line graphs are fallback-only and are not cortical surface renderings. If full arrays or plotting dependencies are missing, the script writes diagnostics and explains how to rerun the real probe.

## Do Not Commit Generated Visual Artifacts

Keep these local:

- `outputs/visualizations/`
- `outputs/*.npz`
- `outputs/*prediction_full*.npz`
- `outputs/*segments.pkl`
- `outputs/*real_tribe_prediction_raw.json`
- `outputs/*real_tribe_segment_stats.json`
