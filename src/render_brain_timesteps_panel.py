from __future__ import annotations

import argparse
import json
import pickle
import traceback
from pathlib import Path
from typing import Any


CAUTION = (
    "Real TRIBE output from synthetic resume-reading events. No human was scanned. "
    "This is not a hiring prediction."
)


def load_prediction_array(path: str | Path):
    import numpy as np

    npz_path = Path(path)
    if not npz_path.exists():
        raise FileNotFoundError(
            "Full prediction array is required. Re-run real TRIBE with --save-full-array."
        )
    data = np.load(npz_path)
    for key in ("prediction", "preds", "arr_0"):
        if key in data:
            return data[key], key
    if not data.files:
        raise ValueError(f"No arrays found in {npz_path}")
    return data[data.files[0]], data.files[0]


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


def timeline_rows(path: str | Path) -> list[dict[str, Any]]:
    return load_json(path).get("segment_timeline", [])


def select_indices(args: argparse.Namespace) -> list[int]:
    if args.section:
        return section_indices(args.timeline, args.section, args.n_timesteps, args.section_window)
    return list(range(args.start_segment, args.start_segment + args.n_timesteps))


def section_indices(timeline_path: str | Path, section: str, n_timesteps: int, window: str) -> list[int]:
    rows = [
        row
        for row in timeline_rows(timeline_path)
        if str(row.get("mapped_section", "")).lower() == section.lower()
        and row.get("segment_index") is not None
    ]
    if not rows:
        raise ValueError(f"No timeline segments found for section: {section}")
    indices = [int(row["segment_index"]) for row in rows]
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
        peak_pos = indices.index(peak_index)
        start = max(0, peak_pos - n_timesteps // 2)
        start = min(start, len(indices) - n_timesteps)
        return indices[start : start + n_timesteps]
    raise ValueError(f"Unsupported section window: {window}")


def resolve_segments(args: argparse.Namespace, indices: list[int], diagnostics: dict[str, Any]):
    segment_objects = load_segment_objects(args.segments_pkl)
    explicit_show_stimuli = args.show_stimuli is not None
    if segment_objects:
        diagnostics["segments_source"] = "segments_pkl"
        diagnostics["show_stimuli_resolved"] = bool(args.show_stimuli)
        return [segment_objects[index] for index in indices if index < len(segment_objects)], bool(args.show_stimuli)
    diagnostics["segments_source"] = "none"
    diagnostics["segments_warning"] = (
        "No full segment objects found; rendering brain panels without stimulus labels."
    )
    if explicit_show_stimuli and args.show_stimuli:
        diagnostics["show_stimuli_warning"] = (
            "--show-stimuli was requested, but full segment objects are unavailable; "
            "using segments=None."
        )
    diagnostics["show_stimuli_resolved"] = False
    print("No full segment objects found; rendering brain panels without stimulus labels.")
    return None, False


def render_panel(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    diagnostics: dict[str, Any] = {
        "prediction_full": args.prediction_full,
        "timeline": args.timeline,
        "segments_pkl": args.segments_pkl,
        "start_segment": args.start_segment,
        "n_timesteps": args.n_timesteps,
        "section": args.section,
        "section_window": args.section_window,
        "output": args.output,
        "cmap": args.cmap,
        "norm_percentile": args.norm_percentile,
        "vmin": args.vmin,
        "dry_run": args.dry_run,
        "caution": CAUTION,
    }
    try:
        preds, array_key = load_prediction_array(args.prediction_full)
        diagnostics["array_key"] = array_key
        diagnostics["prediction_shape"] = list(preds.shape)
        indices = select_indices(args)
        if not indices:
            raise ValueError("No segment indices selected.")
        if max(indices) >= preds.shape[0]:
            raise IndexError(
                f"Selected segment index {max(indices)} exceeds prediction row count {preds.shape[0]}."
            )
        selected_preds = preds[indices]
        diagnostics["selected_segment_indices"] = indices
        diagnostics["selected_prediction_shape"] = list(selected_preds.shape)
        selected_segments, show_stimuli = resolve_segments(args, indices, diagnostics)
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        diagnostics["traceback"] = traceback.format_exc()
        write_diagnostics(output, diagnostics)
        raise

    print(f"Selected segment indices: {indices}")
    print(f"Selected prediction shape: {list(selected_preds.shape)}")
    if args.dry_run:
        write_diagnostics(output, diagnostics)
        print(json.dumps(diagnostics, indent=2))
        return

    try:
        from tribev2.plotting import PlotBrain

        plotter = PlotBrain(mesh="fsaverage5")
        fig = plotter.plot_timesteps(
            selected_preds,
            segments=selected_segments,
            cmap=args.cmap,
            norm_percentile=args.norm_percentile,
            vmin=args.vmin,
            alpha_cmap=(0, 0.2),
            show_stimuli=show_stimuli,
        )
        diagnostics["backend"] = "tribev2_plot_timesteps"
        diagnostics["fig_type"] = f"{type(fig).__module__}.{type(fig).__name__}"
        diagnostics["fig_available_methods"] = available_methods(fig)
        if not save_figure(fig, output, diagnostics):
            raise RuntimeError("PlotBrain returned a figure, but no supported save method succeeded.")
        diagnostics["status"] = "rendered"
    except Exception as exc:
        diagnostics["status"] = "fallback"
        diagnostics["plotbrain_error"] = f"{type(exc).__name__}: {exc}"
        diagnostics["plotbrain_traceback"] = traceback.format_exc()
        create_fallback_vertex_plot(selected_preds, output, diagnostics)
    write_diagnostics(output, diagnostics)
    print(f"Saved brain panel: {output.resolve()}")


def available_methods(fig: Any) -> list[str]:
    return [
        name
        for name in (
            "savefig",
            "screenshot",
            "save_graphic",
            "export_html",
            "write_html",
            "show",
            "close",
            "save",
        )
        if hasattr(fig, name)
    ]


def save_figure(fig: Any, output: Path, diagnostics: dict[str, Any]) -> bool:
    attempts = []
    if hasattr(fig, "savefig"):
        try:
            fig.savefig(str(output), bbox_inches="tight", dpi=200)
            diagnostics["save_method"] = "savefig"
            return True
        except Exception as exc:
            attempts.append({"method": "savefig", "error": f"{type(exc).__name__}: {exc}"})
    for method_name in ("save_graphic", "screenshot"):
        if hasattr(fig, method_name):
            try:
                getattr(fig, method_name)(str(output))
                diagnostics["save_method"] = method_name
                return True
            except Exception as exc:
                attempts.append({"method": method_name, "error": f"{type(exc).__name__}: {exc}"})
    if output.suffix.lower() == ".html" and hasattr(fig, "write_html"):
        try:
            fig.write_html(str(output))
            diagnostics["save_method"] = "write_html"
            return True
        except Exception as exc:
            attempts.append({"method": "write_html", "error": f"{type(exc).__name__}: {exc}"})
    diagnostics["save_attempts"] = attempts
    return False


def create_fallback_vertex_plot(selected_preds, output: Path, diagnostics: dict[str, Any]) -> None:
    import numpy as np

    values = np.mean(selected_preds, axis=0)
    diagnostics["fallback_note"] = "Fallback vertex-value plot, not cortical surface rendering."
    if output.suffix.lower() == ".html":
        from visualization_common import CAUTION_HTML, escape_html, line_chart, plotly_script, write_html

        max_points = 5000
        step = max(1, int(np.ceil(len(values) / max_points)))
        x = list(range(0, len(values), step))
        y = values[x].tolist()
        body = f"""
<h1>{escape_html("Fallback Vertex-Value Plot")}</h1>
{CAUTION_HTML}
{plotly_script()}
<p><strong>Fallback only: this is not cortical surface rendering.</strong></p>
{line_chart("fallback_vertices", x, y, "Fallback vertex values", "Vertex index", "Predicted value")}
"""
        write_html(output, "Fallback Vertex-Value Plot", body)
        return

    import matplotlib.pyplot as plt

    max_points = 5000
    step = max(1, int(np.ceil(len(values) / max_points)))
    x = np.arange(0, len(values), step)
    y = values[x]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(x, y, linewidth=0.8)
    ax.set_title("Fallback vertex-value plot, not cortical surface rendering")
    ax.set_xlabel("Vertex index")
    ax.set_ylabel("Predicted value")
    ax.text(0.01, -0.28, CAUTION, transform=ax.transAxes, fontsize=8, wrap=True)
    fig.tight_layout()
    fig.savefig(str(output), bbox_inches="tight", dpi=200)
    plt.close(fig)


def write_diagnostics(output: Path, diagnostics: dict[str, Any]) -> None:
    path = output.parent / "brain_panel_diagnostics.json"
    path.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Meta-style TRIBE PlotBrain timestep panels.")
    parser.add_argument("--prediction-full", required=True)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--segments-pkl")
    parser.add_argument("--start-segment", type=int, default=0)
    parser.add_argument("--n-timesteps", type=int, default=15)
    parser.add_argument("--section")
    parser.add_argument("--section-window", choices=["first", "middle", "peak"], default="peak")
    parser.add_argument("--show-stimuli", dest="show_stimuli", action="store_true", default=None)
    parser.add_argument("--no-show-stimuli", dest="show_stimuli", action="store_false")
    parser.add_argument("--cmap", default="fire")
    parser.add_argument("--norm-percentile", type=float, default=99)
    parser.add_argument("--vmin", type=float, default=0.6)
    parser.add_argument("--output", required=True, help="PNG, SVG, PDF, or HTML fallback output path.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    render_panel(build_parser().parse_args())


if __name__ == "__main__":
    main()
