"""Safely probe real TRIBE v2 prediction on artificial resume reading events."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

from document_parser import parse_document
from resume_events import (
    build_fake_word_events,
    build_fake_word_events_dataframe,
    prepare_tribe_word_events_dataframe,
    save_events_json,
)
from tribe_output_serializer import save_prediction_or_summary, summarize_object


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "examples" / "resume_sample.txt"
DEFAULT_EVENTS = ROOT / "outputs" / "real_tribe_events.json"
DEFAULT_EVENTS_DF = ROOT / "outputs" / "real_tribe_events_dataframe.csv"
DEFAULT_CANONICAL_DF = ROOT / "outputs" / "real_tribe_events_canonical.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "real_tribe_prediction_raw.json"
DEFAULT_SEGMENTS = ROOT / "outputs" / "real_tribe_segments_summary.json"
DEFAULT_SEGMENT_STATS = ROOT / "outputs" / "real_tribe_segment_stats.json"
DEFAULT_FULL_ARRAY = ROOT / "outputs" / "real_tribe_prediction_full.npz"
DEFAULT_DIAGNOSTICS = ROOT / "outputs" / "real_tribe_probe_diagnostics.json"


def _prefixed_paths(prefix: str | None) -> dict[str, Path]:
    if not prefix:
        return {
            "events": DEFAULT_EVENTS,
            "events_df": DEFAULT_EVENTS_DF,
            "canonical_df": DEFAULT_CANONICAL_DF,
            "output": DEFAULT_OUTPUT,
            "segments": DEFAULT_SEGMENTS,
            "segment_stats": DEFAULT_SEGMENT_STATS,
            "full_array": DEFAULT_FULL_ARRAY,
            "diagnostics": DEFAULT_DIAGNOSTICS,
        }
    outputs = ROOT / "outputs"
    return {
        "events": outputs / f"{prefix}_real_tribe_events.json",
        "events_df": outputs / f"{prefix}_real_tribe_events_dataframe.csv",
        "canonical_df": outputs / f"{prefix}_real_tribe_events_canonical.csv",
        "output": outputs / f"{prefix}_real_tribe_prediction_raw.json",
        "segments": outputs / f"{prefix}_real_tribe_segments_summary.json",
        "segment_stats": outputs / f"{prefix}_real_tribe_segment_stats.json",
        "full_array": outputs / f"{prefix}_real_tribe_prediction_full.npz",
        "diagnostics": outputs / f"{prefix}_real_tribe_probe_diagnostics.json",
    }


def _resolve(path: str | Path) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a guarded real TRIBE v2 probe.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to resume/document.")
    parser.add_argument("--cache-folder", default="./cache_probe")
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Prefix all generated TRIBE output files under outputs/.",
    )
    parser.add_argument(
        "--feature-device",
        default=None,
        help="Device for TRIBE feature extractors. Defaults to --device.",
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--diagnostics", default=None)
    parser.add_argument(
        "--segment-stats-output",
        default=None,
        help="Path for compact per-segment prediction statistics.",
    )
    parser.add_argument(
        "--save-full-array",
        action="store_true",
        help="Also save the full prediction array as compressed NPZ.",
    )
    parser.add_argument(
        "--event-format",
        default="canonical",
        choices=["simple", "dataframe", "canonical"],
        help="Event representation for dry run or real prediction.",
    )
    parser.add_argument(
        "--verbose-errors",
        action="store_true",
        help="Print full traceback and dependency/environment details on failure.",
    )
    parser.add_argument(
        "--text-model-override",
        default=None,
        help=(
            "Experimental: replace TRIBE text_feature.model_name before prediction, "
            "for example unsloth/Llama-3.2-3B-Instruct."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Build events without loading TRIBE.")
    args = parser.parse_args()

    paths = _prefixed_paths(args.output_prefix)
    input_path = _resolve(args.input)
    output_path = _resolve(args.output) if args.output else paths["output"]
    diagnostics_path = _resolve(args.diagnostics) if args.diagnostics else paths["diagnostics"]
    segment_stats_path = (
        _resolve(args.segment_stats_output)
        if args.segment_stats_output
        else paths["segment_stats"]
    )

    diagnostics = {
        "input_path": str(input_path),
        "dry_run": args.dry_run,
        "cache_folder": args.cache_folder,
        "device": args.device,
        "feature_device": args.feature_device or args.device,
        "event_format": args.event_format,
        "output_prefix": args.output_prefix,
        "text_model_override": args.text_model_override,
        "segment_stats_path": str(segment_stats_path),
        "save_full_array": args.save_full_array,
        "caution": (
            "This probe only tests whether TRIBE can produce an output from synthetic "
            "resume reading events. It does not judge resume quality, measure real brain "
            "activity, or predict hiring outcomes."
        ),
        "environment": {
            "uvx_found": shutil.which("uvx") is not None,
            "ffmpeg_found": shutil.which("ffmpeg") is not None,
        },
        "warnings": [],
    }

    try:
        parsed = parse_document(str(input_path))
        events, events_df = _build_events(
            parsed["text"], args.event_format, diagnostics, paths
        )
        diagnostics["document_metadata"] = {
            "source_path": parsed["source_path"],
            "file_type": parsed["file_type"],
            "metadata": parsed["metadata"],
            "warnings": parsed["warnings"],
        }
        diagnostics["events_path"] = str(paths["events"])
        diagnostics["event_count"] = len(events)
        diagnostics["event_preview"] = events[:5]
        diagnostics["final_dataframe"] = _dataframe_diagnostics(events_df)
        print(f"Input: {input_path}")
        print(f"Words/events: {len(events)}")
        print(f"Saved events: {paths['events']}")
        print(f"Saved raw DataFrame: {paths['events_df']}")
        if args.event_format == "canonical":
            print(f"Saved canonical DataFrame: {paths['canonical_df']}")
        print(f"Final DataFrame columns: {list(events_df.columns)}")
        print(events_df.head().to_string(index=False))
        print("First events:")
        for event in events[:5]:
            print(f"- {event}")

        if args.dry_run:
            diagnostics["status"] = "dry_run_complete"
            diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
            diagnostics_path.write_text(
                json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
            )
            print("Dry run complete. TRIBE was not loaded and prediction was not called.")
            print(f"Saved diagnostics: {diagnostics_path}")
            return

        if args.event_format == "simple":
            raise RuntimeError(
                "The simple list-of-dicts format is diagnostic only. Use --event-format dataframe or canonical for real prediction."
            )

        prediction, segments = _run_real_prediction(
            events_df,
            args.cache_folder,
            args.device,
            diagnostics,
            text_model_override=args.text_model_override,
            feature_device=args.feature_device or args.device,
        )
        serialization = save_prediction_or_summary(
            prediction,
            str(output_path),
            str(diagnostics_path),
            save_full_array=args.save_full_array,
            full_array_path=str(paths["full_array"]),
            segment_stats_path=str(segment_stats_path),
        )
        paths["segments"].write_text(
            json.dumps(_serialize_segments(segments), indent=2) + "\n", encoding="utf-8"
        )
        diagnostics["segments_summary_path"] = str(paths["segments"])
        diagnostics["segment_stats_path"] = str(segment_stats_path)
        diagnostics["save_full_array"] = args.save_full_array
        diagnostics["full_array_path"] = serialization.get("full_array_path")
        diagnostics["prediction_shape"] = serialization.get("prediction_shape")
        _merge_diagnostics(diagnostics_path, diagnostics, status="prediction_complete")
        print(f"Saved prediction/summary: {output_path}")
        print(f"Saved diagnostics: {diagnostics_path}")

    except Exception as exc:
        diagnostics["status"] = "failed"
        diagnostics["error"] = _explain_error(exc, traceback.format_exc())
        if args.verbose_errors:
            diagnostics["environment"].update(_verbose_environment(args.device))
        diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostics_path.write_text(
            json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Real TRIBE probe failed: {diagnostics['error']['message']}")
        print("Traceback tail:")
        print("\n".join(diagnostics["error"]["traceback"].splitlines()[-20:]))
        if args.verbose_errors:
            print("Environment:")
            print(json.dumps(diagnostics["environment"], indent=2))
        print(f"Saved diagnostics: {diagnostics_path}")


def _build_events(
    text: str, event_format: str, diagnostics: dict, paths: dict[str, Path]
) -> tuple[list[dict], object]:
    events = build_fake_word_events(text)
    save_events_json(events, str(paths["events"]))
    events_df = build_fake_word_events_dataframe(text)
    paths["events_df"].parent.mkdir(parents=True, exist_ok=True)
    events_df.to_csv(paths["events_df"], index=False)
    diagnostics["raw_dataframe_path"] = str(paths["events_df"])
    diagnostics["raw_dataframe"] = _dataframe_diagnostics(events_df)
    if event_format == "canonical":
        try:
            events_df = prepare_tribe_word_events_dataframe(events_df)
            events_df.to_csv(paths["canonical_df"], index=False)
            diagnostics["canonical_dataframe_path"] = str(paths["canonical_df"])
            diagnostics["canonical_dataframe"] = _dataframe_diagnostics(events_df)
        except Exception:
            diagnostics["canonical_dataframe_error"] = traceback.format_exc()
            raise
    return events, events_df


def _dataframe_diagnostics(events_df) -> dict:
    columns = list(events_df.columns)
    type_counts = (
        events_df["type"].value_counts(dropna=False).to_dict()
        if "type" in events_df.columns
        else {}
    )
    start_min = float(events_df["start"].min()) if "start" in events_df.columns and len(events_df) else None
    end_max = (
        float((events_df["start"] + events_df["duration"]).max())
        if {"start", "duration"}.issubset(events_df.columns) and len(events_df)
        else None
    )
    return {
        "columns": columns,
        "row_count": int(len(events_df)),
        "type_counts": {str(key): int(value) for key, value in type_counts.items()},
        "time_range": {"start": start_min, "end": end_max},
        "word_event_count": int((events_df["type"] == "Word").sum()) if "type" in events_df.columns else 0,
        "text_event_count": int((events_df["type"] == "Text").sum()) if "type" in events_df.columns else 0,
    }


def _run_real_prediction(
    events_df,
    cache_folder: str,
    device: str,
    diagnostics: dict,
    text_model_override: str | None = None,
    feature_device: str = "cpu",
) -> tuple[object, object]:
    started = time.perf_counter()
    try:
        from tribev2.demo_utils import TribeModel
    except Exception as exc:
        raise RuntimeError(
            "Could not import TribeModel from tribev2.demo_utils. Confirm tribev2 is "
            "installed and importable in this Python environment."
        ) from exc

    diagnostics["tribev2_import"] = "ok"
    try:
        model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=cache_folder,
            device=device,
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not load facebook/tribev2. This may be a Hugging Face access, "
            "cache, device, or dependency issue."
        ) from exc

    diagnostics["model_load_seconds"] = round(time.perf_counter() - started, 3)
    if text_model_override:
        _apply_text_model_override(model, text_model_override, diagnostics)
    _force_feature_device(model, feature_device, diagnostics)
    diagnostics["model_summary"] = summarize_object(model)

    predict_started = time.perf_counter()
    if not hasattr(model, "predict"):
        raise RuntimeError("Loaded TribeModel does not expose a predict method.")
    try:
        prediction = model.predict(events_df, verbose=True)
    except Exception:
        diagnostics["prediction_error_stage"] = "model.predict"
        raise

    diagnostics["prediction_seconds"] = round(time.perf_counter() - predict_started, 3)
    diagnostics["prediction_summary"] = summarize_object(prediction)
    if isinstance(prediction, tuple) and len(prediction) == 2:
        return prediction[0], prediction[1]
    return prediction, None


def _serialize_segments(segments: object) -> object:
    if isinstance(segments, list):
        serialized = []
        for index, segment in enumerate(segments):
            if hasattr(segment, "__dict__"):
                item = summarize_object(segment)
                attrs = vars(segment)
                item.update(
                    {
                        "segment_index": index,
                        "start": _safe_float(attrs.get("start")),
                        "duration": _safe_float(attrs.get("duration")),
                        "stop": (
                            _safe_float(attrs.get("start")) + _safe_float(attrs.get("duration"))
                            if attrs.get("start") is not None and attrs.get("duration") is not None
                            else None
                        ),
                        "timeline": attrs.get("timeline"),
                    }
                )
                serialized.append(item)
            elif isinstance(segment, dict):
                serialized.append({**segment, "segment_index": segment.get("segment_index", index)})
            else:
                serialized.append({"segment_index": index, **summarize_object(segment)})
        return serialized
    return summarize_object(segments)


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _merge_diagnostics(path: Path, extra: dict, status: str) -> None:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    merged = {**existing, **extra, "status": status}
    path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")


def _apply_text_model_override(model, model_name: str, diagnostics: dict) -> None:
    text_feature = getattr(getattr(model, "data", None), "text_feature", None)
    if text_feature is None:
        raise RuntimeError("Cannot apply text model override: model.data.text_feature not found.")
    previous = getattr(text_feature, "model_name", None)
    setattr(text_feature, "model_name", model_name)
    diagnostics["text_model_override_applied"] = {
        "previous_model_name": previous,
        "override_model_name": model_name,
        "status": "experimental",
        "caution": (
            "This replaces the text embedding model used by the TRIBE checkpoint. "
            "Outputs are not canonical TRIBE v2 predictions and may be scientifically invalid."
        ),
    }


def _force_feature_device(model, feature_device: str, diagnostics: dict) -> None:
    data = getattr(model, "data", None)
    changes = []
    for attr in [
        "text_feature",
        "audio_feature",
        "video_feature",
        "image_feature",
    ]:
        feature = getattr(data, attr, None)
        if feature is None:
            continue
        previous = getattr(feature, "device", None)
        if previous is not None:
            try:
                setattr(feature, "device", feature_device)
                changes.append(
                    {
                        "feature": attr,
                        "field": "device",
                        "previous": previous,
                        "new": getattr(feature, "device", None),
                    }
                )
            except Exception as exc:
                changes.append(
                    {
                        "feature": attr,
                        "field": "device",
                        "previous": previous,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        infra = getattr(feature, "infra", None)
        if infra is not None and feature_device == "cpu":
            previous_gpus = getattr(infra, "gpus_per_node", None)
            try:
                setattr(infra, "gpus_per_node", 0)
                changes.append(
                    {
                        "feature": attr,
                        "field": "infra.gpus_per_node",
                        "previous": previous_gpus,
                        "new": getattr(infra, "gpus_per_node", None),
                    }
                )
            except Exception as exc:
                changes.append(
                    {
                        "feature": attr,
                        "field": "infra.gpus_per_node",
                        "previous": previous_gpus,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    diagnostics["feature_device_override"] = {
        "requested_feature_device": feature_device,
        "changes": changes,
    }


def _explain_error(exc: Exception, formatted_traceback: str) -> dict:
    message = f"{type(exc).__name__}: {exc}"
    lowered = message.lower()
    likely_causes = []
    if "403" in lowered or "not in the authorized list" in lowered:
        likely_causes.append(
            "Hugging Face token is present, but the account is not authorized for the gated model."
        )
    if "401" in lowered or "token" in lowered:
        likely_causes.append("Hugging Face gated repo or missing/expired token.")
    if "gated" in lowered and not any("gated" in cause.lower() for cause in likely_causes):
        likely_causes.append("Hugging Face gated repo access is required.")
    if "llama" in lowered:
        likely_causes.append("Missing access to the gated LLaMA dependency used by the text path.")
    if "uvx" in lowered:
        likely_causes.append("uvx is missing from PATH.")
    if "ffmpeg" in lowered:
        likely_causes.append("ffmpeg is missing from PATH.")
    if "schema" in lowered or "dataframe" in lowered or "event" in lowered:
        likely_causes.append("The artificial event schema does not match the real TRIBE text pipeline.")
    if not likely_causes:
        likely_causes.append("See repr and traceback context in the terminal output if available.")
    return {
        "class": type(exc).__name__,
        "message": message,
        "repr": repr(exc),
        "likely_causes": likely_causes,
        "traceback": formatted_traceback,
    }


def _verbose_environment(device: str) -> dict:
    hf_cli_token = _huggingface_token_available()
    return {
        "hf_token_set": hf_cli_token
        or bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")),
        "hf_cli_token_available": hf_cli_token,
        "hf_env_token_set": bool(
            os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        ),
        "huggingface_hub_version": _package_version("huggingface_hub"),
        "transformers_version": _package_version("transformers"),
        "torch_version": _package_version("torch"),
        "device": device,
        "python_version": sys.version,
    }


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _huggingface_token_available() -> bool:
    try:
        from huggingface_hub import get_token

        return bool(get_token())
    except Exception:
        return False


if __name__ == "__main__":
    main()
