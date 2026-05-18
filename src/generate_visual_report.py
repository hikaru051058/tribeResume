from __future__ import annotations

import argparse
from pathlib import Path

from visualization_common import CAUTION_HTML, escape_html, load_json, table_html, write_html
from visualize_section_signals import build_section_signals_html
from visualize_timeline import build_timeline_html
from visualize_variant_comparison import build_variant_comparison_html


def build_index(output_dir: Path, timeline: str, features: str, variant_comparison: str | None) -> None:
    timeline_data = load_json(timeline)
    features_data = load_json(features)
    variant_data = load_json(variant_comparison) if variant_comparison else {}

    highest = timeline_data.get("highest_signal_sections", {})
    raw = timeline_data.get("raw_prediction_summary", {})
    metadata = timeline_data.get("metadata", {})
    sections = features_data.get("section_features", [])
    top_sections = sorted(sections, key=lambda row: row.get("cognitive_load_proxy", 0), reverse=True)[:5]

    brain_previews = sorted(output_dir.glob("*brain*.png")) + sorted(output_dir.glob("*brain*.svg"))
    brain_slider = output_dir / "brain_activity_slider.html"
    slider_html = sorted(output_dir.glob("*slider*.html"))
    brain_3d = output_dir / "brain_3d_viewer.html"
    brain_mesh_3d = output_dir / "brain_mesh_3d_viewer.html"
    brain_html = [
        path
        for path in sorted(output_dir.glob("*brain*.html"))
        if path.name not in {brain_slider.name, brain_3d.name, brain_mesh_3d.name}
        and "slider" not in path.name
    ]
    brain_note = "Brain heatmap unavailable. Re-run real TRIBE with --save-full-array."
    if brain_previews:
        brain_note = "Meta-style static brain panel output detected in this directory."
    if brain_slider.exists():
        brain_note = "Interactive brain activity slider detected in this directory."
    if slider_html:
        brain_note = "Interactive brain activity slider output detected in this directory."
    if brain_3d.exists():
        brain_note = "Interactive pseudo-3D brain viewer detected in this directory."
    if brain_mesh_3d.exists():
        brain_note = "Real fsaverage5 browser 3D mesh viewer detected in this directory."
    elif brain_html:
        brain_note = "Only fallback brain HTML output detected. HTML vertex plots are not cortical surface panels."

    links = [
        ("Timeline Analysis", "hikaru_timeline.html"),
        ("Section Signal Dashboard", "hikaru_section_signals.html"),
    ]
    if variant_comparison:
        links.append(("Variant Comparison", "sem_variant_comparison.html"))
    for brain_path in brain_previews[:4]:
        links.append((f"Brain Panel: {brain_path.name}", brain_path.name))
    for slider_path in slider_html:
        links.append((f"Interactive Brain Activity Slider: {slider_path.name}", slider_path.name))
    if brain_3d.exists():
        links.append(("Pseudo-3D Brain Viewer", brain_3d.name))
    if brain_mesh_3d.exists():
        links.append(("Real 3D Cortical Mesh Viewer", brain_mesh_3d.name))
    for brain_path in brain_html[:4]:
        links.append((f"Brain Fallback: {brain_path.name}", brain_path.name))

    preview_html = ""
    if brain_previews:
        cards = []
        for path in brain_previews[:4]:
            cards.append(
                f"""
<div class="card">
  <h3>{escape_html(path.name)}</h3>
  <a href="{escape_html(path.name)}"><img class="preview-img" src="{escape_html(path.name)}" alt="{escape_html(path.name)}"></a>
</div>
"""
            )
        preview_html = f"<h2>Brain Panel Preview</h2><div class=\"grid\">{''.join(cards)}</div>"

    body = f"""
<section class="hero">
<div class="eyebrow">Document Perception Dashboard</div>
<h1>TRIBE Resume Perception Visual Report</h1>
<p class="muted">Interactive timeline, section proxy dashboards, controlled variant comparison, and static brain-panel previews from existing outputs.</p>
</section>
{CAUTION_HTML}
<h2>Visualizations</h2>
<div class="grid">{''.join(f'<a class="card" href="{href}"><strong>{escape_html(label)}</strong><br><span class="muted">{escape_html(href)}</span></a>' for label, href in links)}</div>
<h2>Timeline Analysis Summary</h2>
<div class="grid">
  <div class="card"><div class="muted">Prediction Shape</div><div class="metric">{escape_html(raw.get("prediction_shape"))}</div></div>
  <div class="card"><div class="muted">Retained Segments</div><div class="metric">{escape_html(raw.get("retained_segments"))}</div></div>
  <div class="card"><div class="muted">Exact Stats</div><div class="metric">{escape_html(metadata.get("exact_per_segment_stats_available"))}</div></div>
  <div class="card"><div class="muted">Highest Load Proxy</div><div class="metric">{escape_html(highest.get("highest_load_proxy_section") or highest.get("highest_variance_section"))}</div></div>
</div>
<p><strong>Highest response section:</strong> {escape_html(highest.get("highest_response_section"))}</p>
<h2>Top Cognitive-Load Proxy Sections</h2>
{table_html(top_sections, [("section", "Section"), ("cognitive_load_proxy", "Load Proxy"), ("position_normalized_salience", "Position-Normalized Salience"), ("segment_count", "Segments")])}
<h2>Interactive Brain Activity Slider</h2>
<p>Use the slider view to observe timestep-by-timestep cortical heatmaps with section labels and nearby resume context.</p>
<p><a class="card" href="brain_activity_slider.html"><strong>Open Brain Activity Slider</strong><br><span class="muted">brain_activity_slider.html</span></a></p>
<p><a class="card" href="brain_3d_viewer.html"><strong>Open Pseudo-3D Brain Viewer</strong><br><span class="muted">brain_3d_viewer.html</span></a></p>
<p><a class="card" href="brain_mesh_3d_viewer.html"><strong>Open Real 3D Cortical Mesh Viewer</strong><br><span class="muted">brain_mesh_3d_viewer.html</span></a></p>
<h2>Variant Comparison</h2>
<p>{escape_html(variant_data.get("recommendation", "Variant comparison was not provided."))}</p>
<h2>Brain Heatmap Status</h2>
<p class="callout">{escape_html(brain_note)}</p>
{preview_html}
<pre>python src/run_real_tribe_probe.py \\
  --input path/to/resume.pdf \\
  --cache-folder ./cache_probe \\
  --device cpu \\
  --event-format canonical \\
  --output-prefix hikaru \\
  --save-full-array

python src/render_brain_timesteps_panel.py \\
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \\
  --timeline outputs/hikaru_tribe_timeline_analysis.json \\
  --section experience \\
  --section-window peak \\
  --n-timesteps 15 \\
  --output outputs/visualizations/brain_experience_peak.png</pre>
<pre>python src/render_brain_activity_slider.py \\
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \\
  --timeline outputs/hikaru_tribe_timeline_analysis.json \\
  --events outputs/hikaru_real_tribe_events_canonical.csv \\
  --section experience \\
  --section-window peak \\
  --n-timesteps 15 \\
  --output outputs/visualizations/brain_activity_slider.html</pre>
<pre>python src/build_brain_3d_viewer.py \\
  --slider-diagnostics outputs/visualizations/brain_activity_slider_6view_diagnostics.json \\
  --output outputs/visualizations/brain_3d_viewer.html</pre>
<pre>python src/build_brain_mesh_viewer.py \\
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \\
  --timeline outputs/hikaru_tribe_timeline_analysis.json \\
  --events outputs/hikaru_real_tribe_events_canonical.csv \\
  --section experience \\
  --section-window peak \\
  --n-timesteps 15 \\
  --output outputs/visualizations/brain_mesh_3d_viewer.html</pre>
<h2>Limitations</h2>
<ul>
  <li>Real TRIBE output is from synthetic resume-reading events.</li>
  <li>No human was scanned.</li>
  <li>This is not a hiring prediction.</li>
  <li>Section-level aggregation is a proxy.</li>
</ul>
"""
    write_html(output_dir / "index.html", "TRIBE Resume Perception Visual Report", body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the full Plotly visualization report from existing outputs.")
    parser.add_argument("--timeline", required=True, help="Path to tribe_timeline_analysis.json")
    parser.add_argument("--features", required=True, help="Path to tribe_perception_features.json")
    parser.add_argument("--variant-comparison", help="Path to variant_comparison.json")
    parser.add_argument("--output-dir", required=True, help="Directory for visualization HTML files")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    build_timeline_html(args.timeline, str(output_dir / "hikaru_timeline.html"))
    build_section_signals_html(args.features, str(output_dir / "hikaru_section_signals.html"))
    if args.variant_comparison:
        build_variant_comparison_html(args.variant_comparison, str(output_dir / "sem_variant_comparison.html"))
    build_index(output_dir, args.timeline, args.features, args.variant_comparison)
    print(f"Saved visual report index: {(output_dir / 'index.html').resolve()}")


if __name__ == "__main__":
    main()
