from __future__ import annotations

import argparse
import csv
import json
import pickle
import traceback
from pathlib import Path
from typing import Any

from render_brain_timesteps_panel import load_prediction_array, section_indices, timeline_rows
from visualization_common import CAUTION_HTML, escape_html, write_html


VIEW_PRESETS = {
    "single": ["left"],
    "six": ["left", "right", "medial_left", "medial_right", "dorsal", "ventral"],
    "eight": [
        "left",
        "right",
        "medial_left",
        "medial_right",
        "dorsal",
        "ventral",
        "anterior",
        "posterior",
    ],
}


def select_indices(args: argparse.Namespace) -> list[int]:
    if args.section:
        return section_indices(args.timeline, args.section, args.n_timesteps, args.section_window)
    return list(range(args.start_segment, args.start_segment + args.n_timesteps))


def load_segment_objects(path: str | None) -> list[Any] | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with p.open("rb") as handle:
        return pickle.load(handle)


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
            rows.append(
                {
                    "start": start,
                    "stop": start + duration,
                    "text": row.get("text") or "",
                }
            )
    return rows


def words_for_segment(words: list[dict[str, Any]], start: float | None, stop: float | None) -> str:
    if start is None or stop is None:
        return ""
    selected = [
        word["text"]
        for word in words
        if word["text"] and word["start"] < stop and word["stop"] > start
    ]
    return " ".join(selected)


def resolve_views(args: argparse.Namespace) -> list[str]:
    if args.views:
        return [view.strip() for view in args.views.split(",") if view.strip()]
    return VIEW_PRESETS[args.view_preset]


def render_frame(pred_row, segment_obj: Any | None, output_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {"output": str(output_path)}
    try:
        from tribev2.plotting import PlotBrain

        segments = [segment_obj] if segment_obj is not None else None
        show_stimuli = bool(args.show_stimuli and segment_obj is not None)
        views = resolve_views(args)
        if len(views) == 1:
            neuro = pred_row[None, :]
            views_arg: str | dict[str, str] = views[0]
        else:
            neuro = {view: pred_row[None, :] for view in views}
            views_arg = {view: view for view in views}
        plotter = PlotBrain(mesh="fsaverage5")
        fig = plotter.plot_timesteps(
            neuro,
            segments=segments,
            cmap=args.cmap,
            norm_percentile=args.norm_percentile,
            vmin=args.vmin,
            alpha_cmap=(0, 0.2),
            show_stimuli=show_stimuli,
            views=views_arg,
        )
        diagnostics["backend"] = "tribev2_plot_timesteps"
        diagnostics["views"] = views
        diagnostics["fig_type"] = f"{type(fig).__module__}.{type(fig).__name__}"
        fig.savefig(str(output_path), bbox_inches="tight", dpi=args.dpi)
        diagnostics["status"] = "rendered"
        diagnostics["save_method"] = "savefig"
    except Exception as exc:
        diagnostics["status"] = "failed"
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        diagnostics["traceback"] = traceback.format_exc()
        raise
    return diagnostics


def build_frame_metadata(
    indices: list[int],
    timeline: list[dict[str, Any]],
    frame_paths: list[Path],
    word_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_index = {int(row["segment_index"]): row for row in timeline if row.get("segment_index") is not None}
    frames = []
    for position, (segment_index, frame_path) in enumerate(zip(indices, frame_paths)):
        row = by_index.get(segment_index, {})
        start = row.get("start")
        stop = row.get("stop")
        frames.append(
            {
                "position": position,
                "segment_index": segment_index,
                "image": frame_path.as_posix(),
                "section": row.get("mapped_section") or "unmapped",
                "time_range": f"{_fmt(start)}s - {_fmt(stop)}s",
                "response_abs_mean": row.get("response_abs_mean"),
                "response_std": row.get("response_std"),
                "word_count_in_segment": row.get("word_count_in_segment"),
                "resume_context": words_for_segment(word_events, _float_or_none(start), _float_or_none(stop)),
            }
        )
    return frames


def write_slider_html(output: Path, frames: list[dict[str, Any]], title: str) -> None:
    frames_json = json.dumps(frames)
    body = f"""
<section class="hero">
  <div class="eyebrow">Interactive Brain Activity Viewer</div>
  <h1>{escape_html(title)}</h1>
  <p class="muted">Use the slider to step through TRIBE timesteps. Each frame is a cortical heatmap rendered with PlotBrain.plot_timesteps from existing prediction output. Multi-view mode shows several cortical angles for the same timestep.</p>
</section>
{CAUTION_HTML}
<div class="card">
  <label for="frameSlider"><strong>Timestep</strong></label>
  <input id="frameSlider" type="range" min="0" max="{max(0, len(frames) - 1)}" value="0" step="1" style="width:100%; margin: 12px 0;">
  <div class="grid">
    <div><span class="muted">Segment</span><div class="metric" id="segmentIndex"></div></div>
    <div><span class="muted">Section</span><div class="metric" id="sectionName"></div></div>
    <div><span class="muted">Time</span><div class="metric" id="timeRange"></div></div>
    <div><span class="muted">Response Abs Mean</span><div class="metric" id="responseAbs"></div></div>
  </div>
</div>
<div class="card" style="margin-top:14px;">
  <img id="brainFrame" class="preview-img" alt="Brain activity timestep frame">
</div>
<div class="grid" style="margin-top:14px;">
  <div class="card">
    <h2>Resume Context</h2>
    <p id="resumeContext" style="font-size:16px;"></p>
  </div>
  <div class="card">
    <h2>Frame Stats</h2>
    <table>
      <tbody>
        <tr><th>response_std</th><td id="responseStd"></td></tr>
        <tr><th>word_count_in_segment</th><td id="wordCount"></td></tr>
      </tbody>
    </table>
  </div>
</div>
<script>
const frames = {frames_json};
const slider = document.getElementById("frameSlider");
function fmt(value) {{
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "number") return value.toFixed(4);
  return String(value);
}}
function updateFrame() {{
  const frame = frames[Number(slider.value)];
  document.getElementById("brainFrame").src = frame.image;
  document.getElementById("segmentIndex").textContent = frame.segment_index;
  document.getElementById("sectionName").textContent = frame.section;
  document.getElementById("timeRange").textContent = frame.time_range;
  document.getElementById("responseAbs").textContent = fmt(frame.response_abs_mean);
  document.getElementById("responseStd").textContent = fmt(frame.response_std);
  document.getElementById("wordCount").textContent = fmt(frame.word_count_in_segment);
  document.getElementById("resumeContext").textContent = frame.resume_context || "No word-level context available for this segment.";
}}
slider.addEventListener("input", updateFrame);
updateFrame();
</script>
"""
    write_html(output, title, body)


def render_slider(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_dir = Path(args.frame_dir) if args.frame_dir else output.with_suffix("").parent / f"{output.stem}_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    diagnostics: dict[str, Any] = {
        "prediction_full": args.prediction_full,
        "timeline": args.timeline,
        "events": args.events,
        "segments_pkl": args.segments_pkl,
        "output": args.output,
        "frame_dir": str(frame_dir),
        "section": args.section,
        "section_window": args.section_window,
        "start_segment": args.start_segment,
        "n_timesteps": args.n_timesteps,
        "dry_run": args.dry_run,
        "view_preset": args.view_preset,
        "views": resolve_views(args),
    }
    preds, key = load_prediction_array(args.prediction_full)
    timeline = timeline_rows(args.timeline)
    indices = select_indices(args)
    if not indices:
        raise ValueError("No selected segments.")
    if max(indices) >= preds.shape[0]:
        raise IndexError(f"Selected segment {max(indices)} exceeds prediction rows {preds.shape[0]}.")
    segment_objects = load_segment_objects(args.segments_pkl)
    word_events = load_word_events(args.events)
    diagnostics.update(
        {
            "array_key": key,
            "prediction_shape": list(preds.shape),
            "selected_segment_indices": indices,
            "segments_source": "segments_pkl" if segment_objects else "none",
            "word_events_available": bool(word_events),
        }
    )
    print(f"Selected segment indices: {indices}")
    if args.dry_run:
        write_diagnostics(output, diagnostics)
        print(json.dumps(diagnostics, indent=2))
        return

    frame_paths = []
    frame_diagnostics = []
    for position, index in enumerate(indices):
        view_slug = "-".join(resolve_views(args))
        frame_path = frame_dir / f"frame_{position:03d}_segment_{index:03d}_{view_slug}.png"
        frame_paths.append(frame_path.relative_to(output.parent))
        if frame_path.exists() and args.reuse_frames:
            frame_diagnostics.append({"output": str(frame_path), "status": "reused"})
            continue
        segment_obj = segment_objects[index] if segment_objects and index < len(segment_objects) else None
        frame_diagnostics.append(render_frame(preds[index], segment_obj, frame_path, args))

    frames = build_frame_metadata(indices, timeline, frame_paths, word_events)
    title = args.title or "TRIBE Brain Activity Slider"
    write_slider_html(output, frames, title)
    diagnostics["frames"] = frames
    diagnostics["frame_diagnostics"] = frame_diagnostics
    diagnostics["status"] = "rendered"
    write_diagnostics(output, diagnostics)
    print(f"Saved brain activity slider: {output.resolve()}")


def write_diagnostics(output: Path, diagnostics: dict[str, Any]) -> None:
    path = output.parent / f"{output.stem}_diagnostics.json"
    path.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")


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
    parser = argparse.ArgumentParser(description="Render an interactive slider for TRIBE brain activity timesteps.")
    parser.add_argument("--prediction-full", required=True)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--events", default="outputs/hikaru_real_tribe_events_canonical.csv")
    parser.add_argument("--segments-pkl")
    parser.add_argument("--start-segment", type=int, default=0)
    parser.add_argument("--n-timesteps", type=int, default=15)
    parser.add_argument("--section")
    parser.add_argument("--section-window", choices=["first", "middle", "peak"], default="peak")
    parser.add_argument("--show-stimuli", action="store_true")
    parser.add_argument("--view-preset", choices=sorted(VIEW_PRESETS), default="single")
    parser.add_argument(
        "--views",
        help=(
            "Comma-separated PlotBrain view names. Overrides --view-preset. "
            "Examples: left,right,medial_left,medial_right,dorsal,ventral"
        ),
    )
    parser.add_argument("--cmap", default="fire")
    parser.add_argument("--norm-percentile", type=float, default=99)
    parser.add_argument("--vmin", type=float, default=0.6)
    parser.add_argument("--dpi", type=int, default=170)
    parser.add_argument("--frame-dir")
    parser.add_argument("--reuse-frames", action="store_true")
    parser.add_argument("--title")
    parser.add_argument("--output", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    render_slider(build_parser().parse_args())


if __name__ == "__main__":
    main()
