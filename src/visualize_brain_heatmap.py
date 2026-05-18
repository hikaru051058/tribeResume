from __future__ import annotations

import argparse
import inspect
import json
import pickle
from pathlib import Path
from typing import Any

from visualization_common import CAUTION_HTML, escape_html, line_chart, plotly_script, write_html


def load_prediction_array(path: str | Path):
    import numpy as np

    npz_path = Path(path)
    if not npz_path.exists():
        raise FileNotFoundError(
            "Brain-surface heatmaps require full prediction arrays. "
            "Re-run real TRIBE with --save-full-array."
        )
    data = np.load(npz_path)
    for key in ("prediction", "preds", "arr_0"):
        if key in data:
            return data[key], key
    first_key = data.files[0] if data.files else None
    if first_key is None:
        raise ValueError(f"No arrays found in {npz_path}")
    return data[first_key], first_key


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_segment_objects(path: str | None) -> list[Any] | None:
    if not path:
        return None
    pkl = Path(path)
    if not pkl.exists():
        return None
    with pkl.open("rb") as handle:
        return pickle.load(handle)


def timeline_segments(timeline_path: str | Path) -> list[dict[str, Any]]:
    return load_json(timeline_path).get("segment_timeline", [])


def section_indices(timeline_path: str | Path, section: str, n_timesteps: int, window: str) -> list[int]:
    rows = [
        row
        for row in timeline_segments(timeline_path)
        if str(row.get("mapped_section", "")).lower() == section.lower()
    ]
    indices = [int(row["segment_index"]) for row in rows if row.get("segment_index") is not None]
    if len(indices) <= n_timesteps:
        return indices
    if window == "first":
        return indices[:n_timesteps]
    if window == "middle":
        start = max(0, (len(indices) - n_timesteps) // 2)
        return indices[start : start + n_timesteps]
    if window == "peak":
        peak_row = max(rows, key=lambda row: row.get("response_abs_mean") or 0)
        peak_index = int(peak_row["segment_index"])
        peak_position = indices.index(peak_index)
        start = max(0, peak_position - n_timesteps // 2)
        start = min(start, len(indices) - n_timesteps)
        return indices[start : start + n_timesteps]
    raise ValueError(f"Unsupported section window: {window}")


def aggregate_vectors(array, indices: list[int], aggregate: str):
    import numpy as np

    selected = array[indices]
    if aggregate == "mean":
        return np.mean(selected, axis=0)
    if aggregate == "abs_mean":
        return np.mean(np.abs(selected), axis=0)
    if aggregate == "max":
        return selected[np.argmax(np.mean(np.abs(selected), axis=1))]
    raise ValueError(f"Unsupported aggregate: {aggregate}")


def selected_indices(args: argparse.Namespace) -> list[int]:
    if args.section:
        return section_indices(args.timeline, args.section, args.n_timesteps, args.section_window)
    if args.segment_index is not None:
        return [int(args.segment_index)]
    return list(range(int(args.start_segment), int(args.start_segment) + int(args.n_timesteps)))


def select_segments(
    indices: list[int],
    segment_objects: list[Any] | None,
    timeline_path: str | Path,
    diagnostics: dict[str, Any],
) -> list[Any] | None:
    if segment_objects:
        diagnostics["segments_source"] = "segments_pkl"
        return [segment_objects[index] for index in indices if index < len(segment_objects)]
    summaries = timeline_segments(timeline_path)
    selected = [summaries[index] for index in indices if index < len(summaries)]
    diagnostics["segments_source"] = "timeline_summary_dicts"
    diagnostics["segments_warning"] = (
        "Segments were not full TRIBE segment objects; stimulus labels may be unavailable. "
        "If plot_timesteps rejects summary dictionaries, the visualizer retries with segments=None."
    )
    return selected or None


def try_plot_timesteps(
    selected_preds,
    selected_segments: list[Any] | None,
    output_path: Path,
    args: argparse.Namespace,
    diagnostics: dict[str, Any],
) -> bool:
    try:
        from tribev2.plotting import PlotBrain
    except Exception as exc:
        diagnostics["tribev2_plotbrain_import_error"] = f"{type(exc).__name__}: {exc}"
        return False

    diagnostics["backend"] = "tribev2_plot_timesteps"
    diagnostics["PlotBrain_signature"] = _signature(PlotBrain)
    try:
        plotter = PlotBrain(mesh="fsaverage5")
    except Exception as exc:
        diagnostics["PlotBrain_init_error"] = f"{type(exc).__name__}: {exc}"
        return False

    method = getattr(plotter, "plot_timesteps", None)
    diagnostics["PlotBrain.plot_timesteps_signature"] = _signature(method)
    if method is None:
        diagnostics["PlotBrain_plot_timesteps_error"] = "PlotBrain has no plot_timesteps method."
        return False

    common_kwargs = {
        "cmap": "fire",
        "norm_percentile": 99,
        "vmin": 0.6,
        "alpha_cmap": (0, 0.2),
        "show_stimuli": args.show_stimuli,
    }
    attempts = []
    for segments_arg, source in ((selected_segments, diagnostics.get("segments_source")), (None, "none")):
        try:
            fig = method(selected_preds, segments=segments_arg, **common_kwargs)
            diagnostics["plot_timesteps_segments_attempt"] = source
            diagnostics["returned_fig_type"] = f"{type(fig).__module__}.{type(fig).__name__}"
            diagnostics["returned_fig_methods"] = [
                name
                for name in ("savefig", "write_html", "export_html", "screenshot", "show", "save_graphic", "save")
                if hasattr(fig, name)
            ]
            if save_figure(fig, output_path, args.output_format, diagnostics):
                return True
            diagnostics["save_failure"] = "plot_timesteps returned a figure, but no supported save method succeeded."
            return False
        except Exception as exc:
            attempts.append({"segments_source": source, "error": f"{type(exc).__name__}: {exc}"})
    diagnostics["plot_timesteps_attempts"] = attempts
    return False


def save_figure(fig: Any, output_path: Path, output_format: str, diagnostics: dict[str, Any]) -> bool:
    suffix = output_path.suffix.lower().lstrip(".")
    target_format = suffix if output_format == "auto" and suffix else output_format
    attempts = []
    if target_format == "html":
        for method_name in ("write_html", "export_html", "save"):
            if hasattr(fig, method_name):
                try:
                    getattr(fig, method_name)(str(output_path))
                    diagnostics["save_method"] = method_name
                    return True
                except Exception as exc:
                    attempts.append({"method": method_name, "error": f"{type(exc).__name__}: {exc}"})
    if target_format in ("png", "svg", "pdf", "auto"):
        if hasattr(fig, "savefig"):
            try:
                fig.savefig(str(output_path))
                diagnostics["save_method"] = "savefig"
                return True
            except Exception as exc:
                attempts.append({"method": "savefig", "error": f"{type(exc).__name__}: {exc}"})
        for method_name in ("save_graphic", "save"):
            if hasattr(fig, method_name):
                try:
                    getattr(fig, method_name)(str(output_path))
                    diagnostics["save_method"] = method_name
                    return True
                except Exception as exc:
                    attempts.append({"method": method_name, "error": f"{type(exc).__name__}: {exc}"})
    diagnostics["save_attempts"] = attempts
    return False


def fallback_vertex_plot(values, output_path: Path, title: str) -> None:
    import numpy as np

    arr = np.asarray(values)
    max_points = 5000
    step = max(1, int(np.ceil(len(arr) / max_points)))
    indices = list(range(0, len(arr), step))
    sampled = arr[indices]
    body = f"""
<h1>{escape_html(title)}</h1>
{CAUTION_HTML}
{plotly_script()}
<p><strong>Fallback vertex-value visualization, not cortical surface rendering.</strong></p>
<p>Showing {len(sampled)} of {len(arr)} vertices.</p>
{line_chart("vertex_values", indices, sampled.tolist(), title, "Vertex index", "Predicted value")}
"""
    write_html(output_path, title, body)


def render_heatmap(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    diagnostics: dict[str, Any] = {
        "prediction_full": args.prediction_full,
        "segments_pkl": args.segments_pkl,
        "segments": args.segments,
        "timeline": args.timeline,
        "segment_index": args.segment_index,
        "start_segment": args.start_segment,
        "n_timesteps": args.n_timesteps,
        "section": args.section,
        "section_window": args.section_window,
        "aggregate": args.aggregate,
        "backend_requested": args.backend,
        "output_format": args.output_format,
        "show_stimuli": args.show_stimuli,
        "dry_run": args.dry_run,
        "caution": "Real TRIBE output from synthetic resume-reading events; no human was scanned; not a hiring prediction.",
    }

    try:
        array, key = load_prediction_array(args.prediction_full)
        diagnostics["array_key"] = key
        diagnostics["prediction_shape"] = list(array.shape)
        indices = selected_indices(args)
        diagnostics["selected_segment_indices"] = indices
        if not indices:
            raise ValueError("No segment indices selected.")
        selected_preds = array[indices]
        diagnostics["selected_prediction_shape"] = list(selected_preds.shape)
        segment_objects = load_segment_objects(args.segments_pkl)
        selected_segments = select_segments(indices, segment_objects, args.timeline, diagnostics)
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        _write_diagnostics(output, diagnostics)
        print(diagnostics["error"])
        if isinstance(exc, FileNotFoundError):
            print(_rerun_message())
        return

    if args.dry_run:
        _write_diagnostics(output, diagnostics)
        print(json.dumps(diagnostics, indent=2))
        return

    rendered = False
    if args.backend in ("auto", "tribev2"):
        rendered = try_plot_timesteps(selected_preds, selected_segments, output, args, diagnostics)

    if not rendered:
        if len(indices) == 1:
            values = selected_preds[0]
            title = f"Brain Heatmap Fallback: Segment {indices[0]}"
        else:
            values = aggregate_vectors(array, indices, args.aggregate)
            title = f"Brain Heatmap Fallback: {args.section or 'timesteps'} ({args.aggregate})"
        fallback_vertex_plot(values, output, title)
        diagnostics["fallback_used"] = True
        diagnostics["fallback_note"] = "Fallback vertex-value visualization, not cortical surface rendering."

    _write_diagnostics(output, diagnostics)
    print(f"Saved brain visualization: {output.resolve()}")


def _signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None


def _write_diagnostics(output: Path, diagnostics: dict[str, Any]) -> None:
    path = output.parent / "brain_heatmap_diagnostics.json"
    path.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")


def _rerun_message() -> str:
    return (
        "Brain-surface heatmaps require full prediction arrays. Re-run real TRIBE with:\n"
        "python src/run_real_tribe_probe.py \\\n"
        "  --input path/to/resume.pdf \\\n"
        "  --cache-folder ./cache_probe \\\n"
        "  --device cpu \\\n"
        "  --event-format canonical \\\n"
        "  --output-prefix hikaru \\\n"
        "  --save-full-array \\\n"
        "  --save-segment-objects"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Meta-style TRIBE PlotBrain timestep panels or fallback vertex plots.")
    parser.add_argument("--prediction-full", required=True, help="Compressed .npz file from --save-full-array")
    parser.add_argument("--segments", help="Segments summary JSON, kept for compatibility/diagnostics")
    parser.add_argument("--segments-pkl", help="Pickled full TRIBE segment objects from --save-segment-objects")
    parser.add_argument("--timeline", required=True, help="Timeline analysis JSON")
    parser.add_argument("--segment-index", type=int, default=None, help="Visualize a single segment index")
    parser.add_argument("--start-segment", type=int, default=0, help="First segment for timestep window")
    parser.add_argument("--n-timesteps", type=int, default=15, help="Number of consecutive timesteps")
    parser.add_argument("--section", help="Section name to visualize")
    parser.add_argument("--section-window", choices=["first", "middle", "peak"], default="peak")
    parser.add_argument("--aggregate", choices=["mean", "abs_mean", "max"], default="mean")
    parser.add_argument("--backend", choices=["auto", "tribev2", "nilearn", "plotly"], default="auto")
    parser.add_argument("--show-stimuli", dest="show_stimuli", action="store_true", default=True)
    parser.add_argument("--no-show-stimuli", dest="show_stimuli", action="store_false")
    parser.add_argument("--output-format", choices=["auto", "html", "png", "svg", "pdf"], default="auto")
    parser.add_argument("--dry-run", action="store_true", help="Inspect inputs without rendering")
    parser.add_argument("--output", required=True, help="Output path")
    return parser


def main() -> None:
    render_heatmap(build_parser().parse_args())


if __name__ == "__main__":
    main()
