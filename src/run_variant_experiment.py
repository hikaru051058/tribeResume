"""Run controlled real TRIBE variant experiments."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a controlled two-variant TRIBE perception experiment."
    )
    parser.add_argument("--variant-a", required=True)
    parser.add_argument("--variant-b", required=True)
    parser.add_argument("--cache-folder", default="./cache_probe")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--target-role", default=None)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    output_dir = ROOT / "outputs" / "variant_experiments" / args.output_prefix
    output_dir.mkdir(parents=True, exist_ok=True)
    plans = [
        _variant_plan("a", args.variant_a, args, output_dir),
        _variant_plan("b", args.variant_b, args, output_dir),
    ]

    for plan in plans:
        print(f"\n# Variant {plan['label'].upper()}: {plan['input_path']}")
        for command in plan["commands"]:
            print(_shell_join(command))

    if args.dry_run:
        print("\nDry run complete. No TRIBE or Ollama commands were executed.")
        return

    for plan in plans:
        for command, output_path in zip(plan["commands"], plan["primary_outputs"], strict=True):
            if args.skip_existing and output_path.exists():
                print(f"Skipping existing output: {output_path}")
                continue
            subprocess.run(command, check=True, cwd=ROOT)


def _variant_plan(label: str, input_path: str, args, output_dir: Path) -> dict:
    prefix = f"{args.output_prefix}_{label}"
    file_prefix = f"variant_experiments/{args.output_prefix}/{prefix}"
    resolved_input = _resolve(input_path)
    prediction = output_dir / f"{prefix}_real_tribe_prediction_raw.json"
    segment_stats = output_dir / f"{prefix}_real_tribe_segment_stats.json"
    segments = output_dir / f"{prefix}_real_tribe_segments_summary.json"
    events = output_dir / f"{prefix}_real_tribe_events_canonical.csv"
    timeline = output_dir / f"{prefix}_tribe_timeline_analysis.json"
    features_prefix = str(output_dir / prefix)
    hypotheses = output_dir / f"{prefix}_tribe_perception_hypotheses.json"
    interpretation = output_dir / f"{prefix}_perception_interpretation.json"
    interpretation_md = output_dir / f"{prefix}_perception_interpretation.md"

    return {
        "label": label,
        "input_path": resolved_input,
        "commands": [
            [
                sys.executable,
                str(ROOT / "src" / "run_real_tribe_probe.py"),
                "--input",
                str(resolved_input),
                "--cache-folder",
                args.cache_folder,
                "--device",
                args.device,
                "--event-format",
                "canonical",
                "--output-prefix",
                file_prefix,
            ],
            [
                sys.executable,
                str(ROOT / "src" / "run_tribe_timeline_analysis.py"),
                "--input",
                str(resolved_input),
                "--prediction",
                str(prediction),
                "--segments",
                str(segments),
                "--segment-stats",
                str(segment_stats),
                "--events",
                str(events),
                "--output",
                str(timeline),
            ],
            [
                sys.executable,
                str(ROOT / "src" / "run_tribe_perception_probe.py"),
                "--input",
                str(resolved_input),
                "--real-prediction",
                str(prediction),
                "--segments",
                str(segments),
                "--timeline-analysis",
                str(timeline),
                "--output-prefix",
                features_prefix,
            ],
            [
                sys.executable,
                str(ROOT / "src" / "run_perception_interpretation.py"),
                "--input",
                str(resolved_input),
                "--features",
                str(hypotheses),
                "--model",
                args.model,
                "--target-role",
                args.target_role or "",
                "--output-json",
                str(interpretation),
                "--output-md",
                str(interpretation_md),
            ],
        ],
        "primary_outputs": [prediction, timeline, hypotheses, interpretation],
        "interpretation_md": interpretation_md,
    }


def _resolve(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


def _shell_join(command: list[str]) -> str:
    return " ".join(_quote(part) for part in command)


def _quote(part: str) -> str:
    if not part:
        return "''"
    if any(char.isspace() for char in part):
        return "'" + part.replace("'", "'\"'\"'") + "'"
    return part


if __name__ == "__main__":
    main()
