from __future__ import annotations

import argparse
import inspect
import json
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


KEYWORDS = ("PlotBrain", "plot", "brain", "surface", "fsaverage", "gif", "animation")


def inspect_plotting(probe_return: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "module_available": False,
        "module": "tribev2.plotting",
        "matched_symbols": [],
        "all_public_symbols": [],
        "plotbrain": {},
        "returned_fig_save_methods": {
            "status": "not_rendered",
            "reason": "Inspection does not call plot_timesteps, so returned figure methods cannot be confirmed without rendering.",
            "candidate_methods": [
                "savefig",
                "write_html",
                "export_html",
                "screenshot",
                "show",
                "save_graphic",
                "save",
            ],
        },
        "errors": [],
    }
    try:
        import tribev2.plotting as plotting
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        return result

    result["module_available"] = True
    public = [name for name in dir(plotting) if not name.startswith("_")]
    result["all_public_symbols"] = public
    for name in public:
        obj = getattr(plotting, name, None)
        text = f"{name} {repr(obj)}"
        if any(keyword.lower() in text.lower() for keyword in KEYWORDS):
            item = {"name": name, "repr": repr(obj)[:500], "type": type(obj).__name__}
            try:
                item["signature"] = str(inspect.signature(obj))
            except Exception:
                pass
            result["matched_symbols"].append(item)
    plot_brain = getattr(plotting, "PlotBrain", None)
    if plot_brain is not None:
        result["plotbrain"] = inspect_plotbrain(plot_brain, probe_return=probe_return)
    return result


def inspect_plotbrain(plot_brain: Any, probe_return: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "class_repr": repr(plot_brain),
        "class_signature": _signature(plot_brain),
        "methods": [],
        "plot_timesteps": {},
        "dummy_return_probe": {
            "attempted": False,
            "caution": "Uses a tiny synthetic zero array only to inspect plotting API behavior. This is not TRIBE inference.",
        },
    }
    for name in dir(plot_brain):
        if name.startswith("_"):
            continue
        attr = getattr(plot_brain, name, None)
        if callable(attr):
            data["methods"].append({"name": name, "signature": _signature(attr)})
    plot_timesteps = getattr(plot_brain, "plot_timesteps", None)
    if plot_timesteps is not None:
        data["plot_timesteps"] = {
            "signature": _signature(plot_timesteps),
            "docstring": inspect.getdoc(plot_timesteps),
            "source_excerpt": _source_excerpt(plot_timesteps),
        }
    if probe_return and plot_timesteps is not None:
        data["dummy_return_probe"] = _probe_plot_timesteps_return(plot_brain)
    return data


def _probe_plot_timesteps_return(plot_brain: Any) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "attempted": True,
        "input_shape": [1, 20484],
        "segments": None,
        "show_stimuli": False,
        "caution": "Synthetic zero array only; this does not call TRIBE prediction.",
    }
    try:
        import numpy as np

        plotter = plot_brain(mesh="fsaverage5")
        fig = plotter.plot_timesteps(
            np.zeros((1, 20484), dtype="float32"),
            segments=None,
            cmap="fire",
            norm_percentile=99,
            vmin=0.6,
            alpha_cmap=(0, 0.2),
            show_stimuli=False,
        )
        probe["return_type"] = f"{type(fig).__module__}.{type(fig).__name__}"
        probe["available_methods"] = [
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
        probe["available_attributes"] = [
            name for name in dir(fig) if not name.startswith("_")
        ][:200]
    except Exception as exc:
        probe["error"] = f"{type(exc).__name__}: {exc}"
        probe["traceback"] = traceback.format_exc()
    return probe


def _signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None


def _source_excerpt(obj: Any, max_chars: int = 3000) -> str | None:
    try:
        return inspect.getsource(obj)[:max_chars]
    except Exception:
        return None


def markdown_report(data: dict[str, Any]) -> str:
    lines = [
        "# TRIBE Plotting Inspection",
        "",
        f"- Module available: `{data.get('module_available')}`",
        f"- Module: `{data.get('module')}`",
        "",
    ]
    if data.get("errors"):
        lines += ["## Errors", ""]
        lines += [f"- {error}" for error in data["errors"]]
        lines.append("")
    lines += ["## Matched Symbols", ""]
    if data.get("matched_symbols"):
        for item in data["matched_symbols"]:
            lines.append(f"### {item.get('name')}")
            lines.append(f"- Type: `{item.get('type')}`")
            if item.get("signature"):
                lines.append(f"- Signature: `{item.get('signature')}`")
            lines.append(f"- Repr: `{item.get('repr')}`")
            lines.append("")
    else:
        lines.append("No plotting symbols matched the inspection keywords.")
        lines.append("")
    plotbrain = data.get("plotbrain") or {}
    if plotbrain:
        lines += [
            "## PlotBrain",
            "",
            f"- Class signature: `{plotbrain.get('class_signature')}`",
            "",
            "### Methods",
            "",
        ]
        for method in plotbrain.get("methods", []):
            lines.append(f"- `{method.get('name')}` `{method.get('signature')}`")
        lines += ["", "### plot_timesteps", ""]
        pt = plotbrain.get("plot_timesteps") or {}
        lines.append(f"- Signature: `{pt.get('signature')}`")
        if pt.get("docstring"):
            lines += ["", "Docstring excerpt:", "", "```text", pt["docstring"][:1500], "```"]
        if pt.get("source_excerpt"):
            lines += ["", "Source excerpt:", "", "```python", pt["source_excerpt"], "```"]
        lines.append("")
        probe = plotbrain.get("dummy_return_probe") or {}
        lines += ["", "### Dummy Return Probe", ""]
        lines.append(f"- Attempted: `{probe.get('attempted')}`")
        lines.append(f"- Input shape: `{probe.get('input_shape')}`")
        if probe.get("return_type"):
            lines.append(f"- Return type: `{probe.get('return_type')}`")
        if probe.get("available_methods"):
            lines.append(f"- Available save/display methods: `{probe.get('available_methods')}`")
        if probe.get("error"):
            lines.append(f"- Error: `{probe.get('error')}`")
        lines.append("")
    lines += [
        "## Returned Figure Save Methods",
        "",
        "The inspector does not call `plot_timesteps`, so it cannot confirm the returned figure type without rendering.",
        "The brain visualizer records returned figure methods in diagnostics when rendering is attempted.",
        "",
    ]
    lines += [
        "## Caution",
        "",
        "This only inspects available plotting utilities. It does not render a brain surface and does not call TRIBE prediction.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect availability of tribev2.plotting utilities.")
    parser.add_argument(
        "--skip-return-probe",
        action="store_true",
        help="Do not call PlotBrain.plot_timesteps on a tiny synthetic array.",
    )
    args = parser.parse_args()

    data = inspect_plotting(probe_return=not args.skip_return_probe)
    outputs = ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    json_path = outputs / "tribe_plotting_inspection.json"
    md_path = outputs / "tribe_plotting_inspection.md"
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(data), encoding="utf-8")
    print(f"Plotting available: {data.get('module_available')}")
    print(f"Saved inspection JSON: {json_path}")
    print(f"Saved inspection Markdown: {md_path}")


if __name__ == "__main__":
    main()
