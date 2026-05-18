from __future__ import annotations

import argparse

from visualize_brain_heatmap import render_heatmap


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render an aggregate section brain summary. This is not the same as "
            "Meta-style timestep panels; use visualize_brain_heatmap.py with "
            "--n-timesteps for PlotBrain.plot_timesteps panels."
        )
    )
    parser.add_argument("--prediction-full", required=True, help="Compressed .npz file from --save-full-array")
    parser.add_argument("--timeline", required=True, help="Timeline analysis JSON")
    parser.add_argument("--section", required=True, help="Section name to aggregate")
    parser.add_argument("--segments-pkl", help="Pickled full TRIBE segment objects from --save-segment-objects")
    parser.add_argument("--section-window", choices=["first", "middle", "peak"], default="peak")
    parser.add_argument("--n-timesteps", type=int, default=15)
    parser.add_argument("--aggregate", choices=["mean", "abs_mean", "max"], default="mean")
    parser.add_argument("--backend", choices=["auto", "tribev2", "nilearn", "plotly"], default="auto")
    parser.add_argument("--show-stimuli", dest="show_stimuli", action="store_true", default=False)
    parser.add_argument("--no-show-stimuli", dest="show_stimuli", action="store_false")
    parser.add_argument("--output-format", choices=["auto", "html", "png", "svg", "pdf"], default="auto")
    parser.add_argument("--dry-run", action="store_true", help="Inspect inputs without rendering")
    parser.add_argument("--output", required=True, help="Output HTML path")
    args = parser.parse_args()
    args.segment_index = None
    args.start_segment = 0
    args.segments = None
    render_heatmap(args)


if __name__ == "__main__":
    main()
