from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

from visualization_common import CAUTION_HTML, escape_html, write_html


DEFAULT_VIEW_ORDER = ["left", "right", "medial_left", "medial_right", "dorsal", "ventral"]


FACE_TRANSFORMS = {
    "left": "rotateY(-90deg) translateZ(var(--depth))",
    "right": "rotateY(90deg) translateZ(var(--depth))",
    "medial_left": "translateZ(var(--depth))",
    "medial_right": "rotateY(180deg) translateZ(var(--depth))",
    "dorsal": "rotateX(90deg) translateZ(var(--depth))",
    "ventral": "rotateX(-90deg) translateZ(var(--depth))",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def crop_frame_views(
    frame_path: Path,
    views: list[str],
    output_dir: Path,
    frame_position: int,
    segment_index: int,
) -> dict[str, str]:
    image = Image.open(frame_path).convert("RGBA")
    width, height = image.size
    band_height = height / len(views)
    outputs: dict[str, str] = {}
    for view_index, view in enumerate(views):
        top = int(round(view_index * band_height))
        bottom = int(round((view_index + 1) * band_height))
        crop = image.crop((0, top, width, bottom))
        cropped = crop.getbbox()
        if cropped:
            crop = crop.crop(cropped)
        filename = f"frame_{frame_position:03d}_segment_{segment_index:03d}_{view}.png"
        out_path = output_dir / filename
        crop.save(out_path)
        outputs[view] = filename
    return outputs


def build_viewer(args: argparse.Namespace) -> None:
    diagnostics_path = Path(args.slider_diagnostics)
    diagnostics = load_json(diagnostics_path)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_root = diagnostics_path.parent
    views = diagnostics.get("views") or DEFAULT_VIEW_ORDER
    if args.views:
        views = [view.strip() for view in args.views.split(",") if view.strip()]
    if len(views) != 6:
        raise ValueError("The 3D viewer expects exactly six views.")
    frames = diagnostics.get("frames", [])
    if not frames:
        raise ValueError(f"No frames found in {diagnostics_path}")

    face_dir = Path(args.face_dir) if args.face_dir else output.with_suffix("").parent / f"{output.stem}_faces"
    face_dir.mkdir(parents=True, exist_ok=True)
    viewer_frames = []
    for frame in frames:
        source = frame_root / frame["image"]
        if not source.exists():
            raise FileNotFoundError(f"Missing source frame: {source}")
        faces = crop_frame_views(
            source,
            views,
            face_dir,
            int(frame["position"]),
            int(frame["segment_index"]),
        )
        viewer_frames.append(
            {
                **frame,
                "faces": {
                    view: (face_dir.relative_to(output.parent) / filename).as_posix()
                    for view, filename in faces.items()
                },
            }
        )

    write_viewer_html(output, viewer_frames, views, args.title or "TRIBE Brain 3D View")
    out_diag = {
        "source_slider_diagnostics": str(diagnostics_path),
        "output": str(output),
        "face_dir": str(face_dir),
        "views": views,
        "frame_count": len(viewer_frames),
        "caution": "Pseudo-3D viewer built from six static cortical views per timestep; not a true mesh renderer.",
    }
    output.with_suffix(".diagnostics.json").write_text(json.dumps(out_diag, indent=2) + "\n", encoding="utf-8")
    print(f"Saved 3D brain viewer: {output.resolve()}")


def write_viewer_html(output: Path, frames: list[dict[str, Any]], views: list[str], title: str) -> None:
    frames_json = json.dumps(frames)
    transforms = json.dumps(FACE_TRANSFORMS)
    view_buttons = "".join(
        f'<button class="view-btn" data-view="{escape_html(view)}">{escape_html(view)}</button>'
        for view in views
    )
    face_divs = "\n".join(
        f'<div class="brain-face" id="face-{escape_html(view)}" data-view="{escape_html(view)}"><img alt="{escape_html(view)} view"></div>'
        for view in views
    )
    body = f"""
<style>
  .viewer-shell {{
    display: grid;
    grid-template-columns: minmax(320px, 1fr) 340px;
    gap: 16px;
    align-items: start;
  }}
  .scene {{
    --depth: 190px;
    height: min(620px, 72vh);
    min-height: 430px;
    perspective: 1100px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: radial-gradient(circle at 50% 35%, #ffffff 0, #eef2f6 70%);
    overflow: hidden;
    cursor: grab;
  }}
  .scene:active {{ cursor: grabbing; }}
  .brain-object {{
    position: relative;
    width: min(520px, 72vw);
    height: min(420px, 58vw);
    margin: 86px auto 0;
    transform-style: preserve-3d;
    transform: rotateX(-12deg) rotateY(-24deg);
    transition: transform 120ms linear;
  }}
  .brain-face {{
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    backface-visibility: visible;
    opacity: 0.94;
  }}
  .brain-face img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(0,0,0,.08);
    border-radius: 8px;
    box-shadow: 0 10px 28px rgba(0,0,0,.16);
  }}
  .controls-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0;
  }}
  button.view-btn, button.action-btn {{
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 9px;
    background: #fff;
    color: var(--text);
    cursor: pointer;
  }}
  button.view-btn:hover, button.action-btn:hover {{ background: #eef2f6; }}
  #frameSlider {{ width: 100%; margin: 12px 0; }}
  @media (max-width: 900px) {{
    .viewer-shell {{ grid-template-columns: 1fr; }}
    .scene {{ height: 520px; }}
  }}
</style>
<section class="hero">
  <div class="eyebrow">Pseudo-3D Brain Activity Viewer</div>
  <h1>{escape_html(title)}</h1>
  <p class="muted">This interactable view maps six static cortical angles onto a rotatable 3D object for timestep inspection. It is not a native cortical mesh renderer.</p>
</section>
{CAUTION_HTML}
<div class="viewer-shell">
  <div>
    <div class="scene" id="scene">
      <div class="brain-object" id="brainObject">
        {face_divs}
      </div>
    </div>
    <div class="card" style="margin-top:14px;">
      <label for="frameSlider"><strong>Timestep</strong></label>
      <input id="frameSlider" type="range" min="0" max="{max(0, len(frames)-1)}" value="0" step="1">
      <div class="controls-row">
        {view_buttons}
        <button class="action-btn" id="resetView">Reset</button>
        <button class="action-btn" id="toggleSpin">Auto rotate</button>
      </div>
    </div>
  </div>
  <aside class="card">
    <h2>Current Segment</h2>
    <div class="grid">
      <div><span class="muted">Segment</span><div class="metric" id="segmentIndex"></div></div>
      <div><span class="muted">Section</span><div class="metric" id="sectionName"></div></div>
    </div>
    <p><strong>Time:</strong> <span id="timeRange"></span></p>
    <p><strong>Response abs mean:</strong> <span id="responseAbs"></span></p>
    <p><strong>Response std:</strong> <span id="responseStd"></span></p>
    <h2>Resume Context</h2>
    <p id="resumeContext"></p>
  </aside>
</div>
<script>
const frames = {frames_json};
const transforms = {transforms};
const object = document.getElementById("brainObject");
const scene = document.getElementById("scene");
const slider = document.getElementById("frameSlider");
let rotX = -12;
let rotY = -24;
let dragging = false;
let lastX = 0;
let lastY = 0;
let spinning = false;
let spinHandle = null;

for (const [view, transform] of Object.entries(transforms)) {{
  const face = document.getElementById(`face-${{view}}`);
  if (face) face.style.transform = transform;
}}

function fmt(value) {{
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "number") return value.toFixed(4);
  return String(value);
}}

function applyRotation() {{
  object.style.transform = `rotateX(${{rotX}}deg) rotateY(${{rotY}}deg)`;
}}

function setView(view) {{
  const presets = {{
    left: [-4, 78],
    right: [-4, -78],
    medial_left: [-8, 0],
    medial_right: [-8, 180],
    dorsal: [-82, 0],
    ventral: [82, 0],
  }};
  if (!presets[view]) return;
  [rotX, rotY] = presets[view];
  applyRotation();
}}

function updateFrame() {{
  const frame = frames[Number(slider.value)];
  for (const [view, src] of Object.entries(frame.faces)) {{
    const img = document.querySelector(`#face-${{view}} img`);
    if (img) img.src = src;
  }}
  document.getElementById("segmentIndex").textContent = frame.segment_index;
  document.getElementById("sectionName").textContent = frame.section;
  document.getElementById("timeRange").textContent = frame.time_range;
  document.getElementById("responseAbs").textContent = fmt(frame.response_abs_mean);
  document.getElementById("responseStd").textContent = fmt(frame.response_std);
  document.getElementById("resumeContext").textContent = frame.resume_context || "No word-level context available.";
}}

scene.addEventListener("pointerdown", event => {{
  dragging = true;
  lastX = event.clientX;
  lastY = event.clientY;
  scene.setPointerCapture(event.pointerId);
}});
scene.addEventListener("pointermove", event => {{
  if (!dragging) return;
  const dx = event.clientX - lastX;
  const dy = event.clientY - lastY;
  lastX = event.clientX;
  lastY = event.clientY;
  rotY += dx * 0.45;
  rotX -= dy * 0.35;
  rotX = Math.max(-88, Math.min(88, rotX));
  applyRotation();
}});
scene.addEventListener("pointerup", () => {{ dragging = false; }});
scene.addEventListener("pointercancel", () => {{ dragging = false; }});
slider.addEventListener("input", updateFrame);
document.querySelectorAll(".view-btn").forEach(button => {{
  button.addEventListener("click", () => setView(button.dataset.view));
}});
document.getElementById("resetView").addEventListener("click", () => {{
  rotX = -12;
  rotY = -24;
  applyRotation();
}});
document.getElementById("toggleSpin").addEventListener("click", () => {{
  spinning = !spinning;
  if (spinning) {{
    spinHandle = setInterval(() => {{
      rotY += 1.2;
      applyRotation();
    }}, 40);
  }} else {{
    clearInterval(spinHandle);
  }}
}});

updateFrame();
applyRotation();
</script>
"""
    write_html(output, title, body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a pseudo-3D rotatable brain viewer from six-view slider frames.")
    parser.add_argument(
        "--slider-diagnostics",
        required=True,
        help="Diagnostics JSON from render_brain_activity_slider.py with --view-preset six.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--face-dir")
    parser.add_argument("--views", help="Optional comma-separated six-view order.")
    parser.add_argument("--title")
    return parser


def main() -> None:
    build_viewer(build_parser().parse_args())


if __name__ == "__main__":
    main()
