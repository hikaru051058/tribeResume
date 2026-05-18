from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from render_brain_timesteps_panel import load_prediction_array, section_indices, timeline_rows
from visualization_common import CAUTION_HTML, escape_html, write_html


COLOR_SCALES = {
    "activity": [
        [0.0, "#ffffff"],
        [0.10, "#f8fafc"],
        [0.20, "#e5e7eb"],
        [0.25, "#7f1d1d"],
        [0.45, "#dc2626"],
        [0.68, "#f97316"],
        [0.84, "#facc15"],
        [1.0, "#fff7ed"],
    ],
    "fire": [
        [0.0, "#000000"],
        [0.18, "#3b0a0a"],
        [0.38, "#991b1b"],
        [0.62, "#f97316"],
        [0.82, "#fde047"],
        [1.0, "#ffffff"],
    ],
    "signed": [
        [0.0, "#2563eb"],
        [0.22, "#60a5fa"],
        [0.5, "#f8fafc"],
        [0.72, "#fb923c"],
        [1.0, "#dc2626"],
    ],
}


def load_word_events(path: str | None) -> list[dict[str, Any]]:
    if not path or not Path(path).exists():
        return []
    rows: list[dict[str, Any]] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("type") != "Word":
                continue
            try:
                start = float(row.get("start") or 0)
                duration = float(row.get("duration") or 0)
            except ValueError:
                continue
            rows.append({"start": start, "stop": start + duration, "text": row.get("text") or ""})
    return rows


def words_for_segment(words: list[dict[str, Any]], start: float | None, stop: float | None) -> str:
    if start is None or stop is None:
        return ""
    return " ".join(
        word["text"] for word in words if word["text"] and word["start"] < stop and word["stop"] > start
    )


def select_indices(args: argparse.Namespace) -> list[int]:
    if args.section:
        return section_indices(args.timeline, args.section, args.n_timesteps, args.section_window)
    return list(range(args.start_segment, args.start_segment + args.n_timesteps))


def normalize_values(values: np.ndarray, percentile: float, value_mode: str) -> np.ndarray:
    if value_mode == "absolute":
        source = np.abs(values)
        limit = float(np.nanpercentile(source, percentile))
        if not limit or np.isnan(limit):
            limit = 1.0
        return np.clip(source / limit, 0, 1).astype("float32")
    limit = float(np.nanpercentile(np.abs(values), percentile))
    if not limit or np.isnan(limit):
        limit = 1.0
    clipped = np.clip(values, -limit, limit)
    return (clipped / limit).astype("float32")


def mesh_payload(
    preds: np.ndarray,
    indices: list[int],
    timeline_path: str,
    events_path: str | None,
    percentile: float,
    value_mode: str,
) -> dict[str, Any]:
    from tribev2.plotting import PlotBrain

    plotter = PlotBrain(mesh="fsaverage5")
    mesh = plotter._mesh["both"]
    coords = np.asarray(mesh["coords"], dtype="float32")
    faces = np.asarray(mesh["faces"], dtype="int32")
    timeline = timeline_rows(timeline_path)
    by_index = {int(row["segment_index"]): row for row in timeline if row.get("segment_index") is not None}
    words = load_word_events(events_path)
    selected = preds[indices]
    normed = normalize_values(selected, percentile, value_mode)
    frames = []
    for position, segment_index in enumerate(indices):
        row = by_index.get(segment_index, {})
        start = _float_or_none(row.get("start"))
        stop = _float_or_none(row.get("stop"))
        frames.append(
            {
                "name": str(position),
                "segment_index": segment_index,
                "section": row.get("mapped_section") or "unmapped",
                "time_range": f"{_fmt(start)}s - {_fmt(stop)}s",
                "response_abs_mean": row.get("response_abs_mean"),
                "response_std": row.get("response_std"),
                "resume_context": words_for_segment(words, start, stop),
                "intensity": normed[position].round(5).tolist(),
            }
        )
    return {
        "coords": coords.round(5).tolist(),
        "faces": faces.tolist(),
        "frames": frames,
        "selected_segment_indices": indices,
        "prediction_shape": list(preds.shape),
        "normalization": {
            "method": f"{value_mode} percentile clipping",
            "percentile": percentile,
            "range": [0, 1] if value_mode == "absolute" else [-1, 1],
            "value_mode": value_mode,
        },
    }


def write_mesh_html(
    output: Path,
    payload: dict[str, Any],
    title: str,
    colorscale_name: str,
    surface_opacity: float,
    scene_bgcolor: str,
) -> None:
    coords = payload["coords"]
    faces = payload["faces"]
    x = [row[0] for row in coords]
    y = [row[1] for row in coords]
    z = [row[2] for row in coords]
    i = [row[0] for row in faces]
    j = [row[1] for row in faces]
    k = [row[2] for row in faces]
    frames = payload["frames"]
    base_intensity = frames[0]["intensity"]
    value_mode = payload["normalization"]["value_mode"]
    colorscale = COLOR_SCALES[colorscale_name]
    color_min, color_max = (0, 1) if value_mode == "absolute" else (-1, 1)
    colorbar_title = "Activity magnitude" if value_mode == "absolute" else "Signed response"
    frames_js = [
        {
            "name": frame["name"],
            "data": [{"intensity": frame["intensity"]}],
            "layout": {"title": f"{title}: segment {frame['segment_index']}"},
        }
        for frame in frames
    ]
    meta_js = json.dumps([{key: value for key, value in frame.items() if key != "intensity"} for frame in frames])
    body = f"""
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  .mesh-viewer {{
    display: grid;
    grid-template-columns: minmax(620px, 1fr) 330px;
    gap: 16px;
    align-items: start;
  }}
  .mesh-stage {{
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  #meshPlot {{
    width: 100%;
    height: min(820px, 82vh);
  }}
  .mesh-side {{
    position: sticky;
    top: 72px;
    display: grid;
    gap: 12px;
  }}
  .control-row {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
  }}
  .mesh-button {{
    border: 1px solid var(--border);
    background: #fff;
    border-radius: 6px;
    padding: 7px 9px;
    cursor: pointer;
  }}
  .mesh-button:hover {{ background: #eef2f6; }}
  #timeSlider {{ width: 100%; margin: 8px 0 4px; }}
  .context-box {{
    max-height: 170px;
    overflow: auto;
    padding: 10px;
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 6px;
  }}
  @media (max-width: 980px) {{
    .mesh-viewer {{ grid-template-columns: 1fr; }}
    .mesh-side {{ position: static; }}
    #meshPlot {{ height: 620px; }}
  }}
</style>
<section class="hero">
  <div class="eyebrow">Real 3D Cortical Mesh Viewer</div>
  <h1>{escape_html(title)}</h1>
  <p class="muted">TRIBE prediction values are mapped directly onto the fsaverage5 cortical mesh vertices. Drag to rotate and use the slider to move through timesteps. Default color shows activity magnitude after percentile normalization.</p>
</section>
{CAUTION_HTML}
<div class="mesh-viewer">
  <div class="mesh-stage">
    <div id="meshPlot"></div>
  </div>
  <aside class="mesh-side">
    <div class="card">
      <h2>Time</h2>
      <input id="timeSlider" type="range" min="0" max="{len(frames)-1}" value="0" step="1">
      <div class="grid">
        <div><span class="muted">Segment</span><div class="metric" id="segmentIndex"></div></div>
        <div><span class="muted">Section</span><div class="metric" id="sectionName"></div></div>
      </div>
      <p><strong>Time range:</strong> <span id="timeRange"></span></p>
      <p><strong>Response abs mean:</strong> <span id="responseAbs"></span></p>
      <p><strong>Response std:</strong> <span id="responseStd"></span></p>
    </div>
    <div class="card">
      <h2>Camera</h2>
      <div class="control-row">
        <button class="mesh-button" data-camera="left">Left</button>
        <button class="mesh-button" data-camera="right">Right</button>
        <button class="mesh-button" data-camera="top">Top</button>
        <button class="mesh-button" data-camera="front">Front</button>
        <button class="mesh-button" data-camera="reset">Reset</button>
      </div>
      <p class="muted">Drag the mesh to rotate. Scroll to zoom.</p>
    </div>
    <div class="card">
      <h2>Display</h2>
      <p><strong>Color:</strong> {escape_html(value_mode)} / {escape_html(colorscale_name)}</p>
      <p><strong>Normalization:</strong> p{escape_html(payload["normalization"]["percentile"])}</p>
      <p><strong>Mesh:</strong> {escape_html(len(coords))} vertices, {escape_html(len(faces))} faces</p>
      <p><strong>Prediction:</strong> {escape_html(payload.get("prediction_shape"))}</p>
    </div>
    <div class="card">
      <h2>Resume Context</h2>
      <div class="context-box" id="resumeContext"></div>
    </div>
  </div>
</div>
<script>
const frameMeta = {meta_js};
const trace = {{
  type: "mesh3d",
  x: {json.dumps(x)},
  y: {json.dumps(y)},
  z: {json.dumps(z)},
  i: {json.dumps(i)},
  j: {json.dumps(j)},
  k: {json.dumps(k)},
  intensity: {json.dumps(base_intensity)},
  colorscale: {json.dumps(colorscale)},
  cmin: {color_min},
  cmax: {color_max},
  opacity: {surface_opacity},
  showscale: true,
  colorbar: {{
    title: {json.dumps(colorbar_title)},
    titleside: "right",
    tickfont: {{color: "#111827"}},
    titlefont: {{color: "#111827"}}
  }},
  lighting: {{ambient: 0.28, diffuse: 0.82, specular: 0.32, roughness: 0.72, fresnel: 0.18}},
  lightposition: {{x: 140, y: 180, z: 90}},
  flatshading: false,
  hoverinfo: "skip"
}};
const frames = {json.dumps(frames_js)};
const layout = {{
  paper_bgcolor: "white",
  plot_bgcolor: "white",
  margin: {{l: 0, r: 0, t: 0, b: 0}},
  scene: {{
    aspectmode: "data",
    bgcolor: {json.dumps(scene_bgcolor)},
    xaxis: {{visible: false}},
    yaxis: {{visible: false}},
    zaxis: {{visible: false}},
    camera: {{eye: {{x: 1.5, y: -1.5, z: 0.8}}}}
  }}
}};
Plotly.newPlot("meshPlot", [trace], layout, {{responsive: true, displaylogo: false, scrollZoom: true}}).then(() => {{
  Plotly.addFrames("meshPlot", frames);
}});
function fmt(value) {{
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "number") return value.toFixed(4);
  return String(value);
}}
function updateMeta(index) {{
  const frame = frameMeta[index];
  document.getElementById("segmentIndex").textContent = frame.segment_index;
  document.getElementById("sectionName").textContent = frame.section;
  document.getElementById("timeRange").textContent = frame.time_range;
  document.getElementById("responseAbs").textContent = fmt(frame.response_abs_mean);
  document.getElementById("responseStd").textContent = fmt(frame.response_std);
  document.getElementById("resumeContext").textContent = frame.resume_context || "No word-level context available.";
}}
const cameras = {{
  left: {{eye: {{x: -1.8, y: 0, z: 0.35}}}},
  right: {{eye: {{x: 1.8, y: 0, z: 0.35}}}},
  top: {{eye: {{x: 0, y: 0, z: 2.2}}}},
  front: {{eye: {{x: 0, y: -2.0, z: 0.45}}}},
  reset: {{eye: {{x: 1.5, y: -1.5, z: 0.8}}}},
}};
document.querySelectorAll("[data-camera]").forEach(button => {{
  button.addEventListener("click", () => {{
    Plotly.relayout("meshPlot", {{"scene.camera": cameras[button.dataset.camera]}});
  }});
}});
document.getElementById("timeSlider").addEventListener("input", event => {{
  const index = Number(event.target.value);
  Plotly.animate("meshPlot", [String(index)], {{
    mode: "immediate",
    transition: {{duration: 0}},
    frame: {{duration: 0, redraw: true}}
  }});
  updateMeta(index);
}});
updateMeta(0);
</script>
"""
    write_html(output, title, body)


def build_viewer(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    preds, key = load_prediction_array(args.prediction_full)
    indices = select_indices(args)
    if not indices:
        raise ValueError("No selected segments.")
    if max(indices) >= preds.shape[0]:
        raise IndexError(f"Selected segment {max(indices)} exceeds prediction rows {preds.shape[0]}.")
    payload = mesh_payload(
        preds,
        indices,
        args.timeline,
        args.events,
        args.norm_percentile,
        args.value_mode,
    )
    title = args.title or "TRIBE 3D Cortical Activity Viewer"
    write_mesh_html(output, payload, title, args.colorscale, args.surface_opacity, args.scene_bgcolor)
    diagnostics = {
        "prediction_full": args.prediction_full,
        "array_key": key,
        "timeline": args.timeline,
        "events": args.events,
        "output": args.output,
        "selected_segment_indices": indices,
        "prediction_shape": list(preds.shape),
        "vertices": len(payload["coords"]),
        "faces": len(payload["faces"]),
        "normalization": payload["normalization"],
        "colorscale": args.colorscale,
        "surface_opacity": args.surface_opacity,
        "scene_bgcolor": args.scene_bgcolor,
        "caution": "Real 3D mesh viewer for model-predicted TRIBE output from synthetic resume-reading events.",
    }
    output.with_suffix(".diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    print(f"Saved real 3D mesh viewer: {output.resolve()}")


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    numeric = _float_or_none(value)
    if numeric is None:
        return ""
    return f"{numeric:.2f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an actual browser 3D fsaverage5 mesh viewer for TRIBE predictions.")
    parser.add_argument("--prediction-full", required=True)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--events", default="outputs/hikaru_real_tribe_events_canonical.csv")
    parser.add_argument("--start-segment", type=int, default=0)
    parser.add_argument("--n-timesteps", type=int, default=15)
    parser.add_argument("--section")
    parser.add_argument("--section-window", choices=["first", "middle", "peak"], default="peak")
    parser.add_argument("--norm-percentile", type=float, default=99)
    parser.add_argument("--value-mode", choices=["absolute", "signed"], default="absolute")
    parser.add_argument("--colorscale", choices=sorted(COLOR_SCALES), default="activity")
    parser.add_argument("--surface-opacity", type=float, default=1.0)
    parser.add_argument("--scene-bgcolor", default="rgba(0,0,0,0)")
    parser.add_argument("--title")
    parser.add_argument("--output", required=True)
    return parser


def main() -> None:
    build_viewer(build_parser().parse_args())


if __name__ == "__main__":
    main()
