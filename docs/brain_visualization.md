# Brain Visualization

## What fsaverage5 Means

`fsaverage5` is a common lower-resolution cortical surface mesh used for brain visualization. At a high level, it provides a standardized surface where vertex values can be plotted across an average brain geometry.

TRIBE prediction outputs are shaped like:

```text
(n_segments, n_vertices_or_response_dimensions)
```

The observed resume output used:

```text
[182, 20484]
```

The second dimension is approximately 20k response dimensions, which is consistent with a cortical-surface-style vertex vector. These dimensions are not resume labels.

## Meta-Style PlotBrain Path

The official Meta-style plotting path from the TRIBE demo is:

```python
from tribev2.plotting import PlotBrain

plotter = PlotBrain(mesh="fsaverage5")

n_timesteps = 15
fig = plotter.plot_timesteps(
    preds[:n_timesteps],
    segments=segments[:n_timesteps],
    cmap="fire",
    norm_percentile=99,
    vmin=.6,
    alpha_cmap=(0, .2),
    show_stimuli=True,
)
```

The local `render_brain_timesteps_panel.py` script uses this `PlotBrain.plot_timesteps` path directly and targets static PNG/SVG/PDF output. This is the preferred notebook-like renderer.

`visualize_brain_heatmap.py` can still produce fallback HTML vertex plots, but those HTML line graphs are not cortical-surface renderings.

## Timestep Heatmap

A timestep heatmap visualizes one or more prediction vectors:

```text
preds[start_segment:start_segment+n_timesteps]
```

It may show which response dimensions had high positive or negative predicted values for specific synthetic reading time segments.

It does not show measured brain activity. It is model output from a synthetic text stimulus.

## Section-Average Heatmap

A section-average heatmap first maps timeline segments to a resume section, then aggregates vectors:

```text
mean(preds[section_segment_indices], axis=0)
```

Supported aggregation modes:

- `mean`
- `abs_mean`
- `max`

This is a section-level product proxy. It is not a native TRIBE section label. Aggregate section summaries are different from Meta-style timestep panels.

## Required Files

Best Meta-style heatmap output requires:

- full prediction `.npz`
- optional full segment object `.pkl` for stimulus labels
- available `tribev2.plotting.PlotBrain`

Compact per-segment stats are enough for timeline dashboards but not brain surfaces.

If only the `.npz` is available, the brain surface can still be attempted with `segments=None`, but stimulus labels may not appear. If both `.npz` and `.pkl` are available, `show_stimuli=True` is more likely to match the demo notebook behavior.

## Commands

Run real TRIBE and save full arrays plus segment objects:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix hikaru \
  --save-full-array \
  --save-segment-objects
```

Visualize the first 15 timesteps like the Meta demo:

```bash
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --start-segment 0 \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_first_15.png
```

Visualize an experience-section peak window:

```bash
python src/render_brain_timesteps_panel.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_experience_peak.png
```

If full segment objects were saved with `--save-segment-objects`, pass them to show stimulus labels:

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

Use `visualize_section_brain_summary.py` for aggregate/fallback section summaries and `render_brain_timesteps_panel.py` for Meta-style `plot_timesteps` panels.

## Interactive Time Slider

For a browser-based timestep viewer, render individual PlotBrain frames and wrap them in an HTML slider:

```bash
python src/render_brain_activity_slider.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --events outputs/hikaru_real_tribe_events_canonical.csv \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --output outputs/visualizations/brain_activity_slider.html
```

Open it with:

```bash
open outputs/visualizations/brain_activity_slider.html
```

The slider shows one cortical frame at a time with the mapped section, segment index, response statistics, and nearby resume words from the canonical event CSV.

To view several cortical angles per timestep, use the six-view preset:

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
```

The six-view preset renders `left`, `right`, `medial_left`, `medial_right`, `dorsal`, and `ventral` rows for each slider position. This approximates a 3D inspection workflow from static cortical views; it is not a true rotatable 3D model.

To build a browser-rotatable pseudo-3D viewer from those six views:

```bash
python src/build_brain_3d_viewer.py \
  --slider-diagnostics outputs/visualizations/brain_activity_slider_6view_diagnostics.json \
  --output outputs/visualizations/brain_3d_viewer.html

open outputs/visualizations/brain_3d_viewer.html
```

This maps the six static views onto a rotatable CSS 3D object. It is useful for interactive inspection, but it is not a native cortical mesh and should not be treated as anatomically exact 3D geometry.

For an actual browser 3D cortical mesh, use the fsaverage5 mesh coordinates and faces exposed by `PlotBrain`:

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

This maps TRIBE prediction values directly onto the 20,484 fsaverage5 vertices and uses Plotly `mesh3d` for rotation and timestep animation.

The default mesh viewer uses `--value-mode absolute` because activity magnitude is easier to inspect than signed response values. Use `--value-mode signed --colorscale signed` if you want to inspect positive vs negative model response direction.

## Fallback Vertex Plot

If `tribev2.plotting.PlotBrain` or its dependencies are unavailable, or if the returned figure cannot be saved, the visualizer produces a vertex-value line chart. This is not cortical surface rendering. It is only a fallback view of predicted values by vertex index.

## Limitations

- The input is synthetic resume-reading events, not naturalistic reading behavior.
- No human was scanned.
- Outputs are predictions from an average model, not individual brain data.
- The system does not predict hiring outcomes.
- Section aggregation depends on synthetic timing and section mapping.
- Full arrays are required for heatmaps.

## Safety

Do not commit full prediction arrays, segment pickles, raw predictions, or generated visual artifacts:

```gitignore
outputs/*.npz
outputs/*prediction_full*.npz
outputs/*segments.pkl
outputs/*real_tribe_prediction_raw.json
outputs/*real_tribe_segment_stats.json
outputs/visualizations/
```
