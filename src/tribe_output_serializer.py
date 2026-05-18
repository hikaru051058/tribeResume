"""Serialization helpers for real TRIBE probe diagnostics."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def to_json_safe(obj: Any) -> Any:
    """Convert common Python, numpy, torch, and object values into JSON-safe data."""

    if obj is None or isinstance(obj, str | int | float | bool):
        return obj
    if isinstance(obj, dict):
        return {str(key): to_json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple):
        return [to_json_safe(value) for value in obj]

    if _is_torch_tensor(obj):
        return _array_summary(obj.detach().cpu().numpy())
    if hasattr(obj, "tolist"):
        try:
            return _array_summary(obj)
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {
            "type": type(obj).__name__,
            "attributes": to_json_safe(vars(obj)),
        }
    return summarize_object(obj)


def _array_summary(obj: Any) -> dict:
    """Summarize array/tensor-like data without dumping giant payloads."""

    try:
        import numpy as np

        array = np.asarray(obj)
        finite = array[np.isfinite(array)] if np.issubdtype(array.dtype, np.number) else []
        summary = {
            "type": type(obj).__name__,
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "size": int(array.size),
        }
        if len(finite):
            summary.update(
                {
                    "min": _clean_float(float(np.min(finite))),
                    "max": _clean_float(float(np.max(finite))),
                    "mean": _clean_float(float(np.mean(finite))),
                    "std": _clean_float(float(np.std(finite))),
                }
            )
        if array.size <= 200:
            summary["values"] = to_json_safe(array.tolist())
        else:
            preview = array.reshape(-1, array.shape[-1])[:5] if array.ndim > 1 else array[:20]
            summary["preview"] = to_json_safe(preview.tolist())
        return summary
    except Exception:
        return summarize_object(obj)


def _clean_float(value: float) -> float | None:
    if math.isnan(value) or math.isinf(value):
        return None
    return round(value, 6)


def summarize_object(obj: Any) -> dict:
    """Return a compact structural summary for non-serializable objects."""

    summary = {
        "type": f"{type(obj).__module__}.{type(obj).__name__}",
        "repr_preview": repr(obj)[:1000],
    }
    if isinstance(obj, dict):
        summary["keys"] = [str(key) for key in obj.keys()]
    if hasattr(obj, "keys"):
        try:
            summary["keys"] = [str(key) for key in obj.keys()]
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            summary["attributes"] = sorted(str(key) for key in vars(obj).keys())
        except Exception:
            pass
    if hasattr(obj, "shape"):
        try:
            summary["shape"] = list(obj.shape)
        except Exception:
            summary["shape"] = str(getattr(obj, "shape"))
    if hasattr(obj, "dtype"):
        summary["dtype"] = str(getattr(obj, "dtype"))
    return summary


def compute_prediction_segment_stats(preds: Any) -> dict:
    """Compute compact global and per-segment stats for a TRIBE prediction array."""

    import numpy as np

    array = np.asarray(preds)
    if array.ndim != 2:
        raise ValueError(
            f"Expected a 2D prediction array shaped (segments, dimensions), got {array.shape}"
        )
    finite = array[np.isfinite(array)] if np.issubdtype(array.dtype, np.number) else array
    per_segment = []
    for segment_index, row in enumerate(array):
        row = np.asarray(row)
        abs_row = np.abs(row)
        top_indices = np.argsort(abs_row)[-5:][::-1]
        per_segment.append(
            {
                "segment_index": segment_index,
                "response_mean": _clean_float(float(np.mean(row))),
                "response_abs_mean": _clean_float(float(np.mean(abs_row))),
                "response_std": _clean_float(float(np.std(row))),
                "response_min": _clean_float(float(np.min(row))),
                "response_max": _clean_float(float(np.max(row))),
                "response_l2_norm": _clean_float(float(np.linalg.norm(row))),
                "positive_fraction": _clean_float(float(np.mean(row > 0))),
                "negative_fraction": _clean_float(float(np.mean(row < 0))),
                "top_abs_values_preview": [
                    {
                        "vertex_index": int(index),
                        "value": _clean_float(float(row[index])),
                        "abs_value": _clean_float(float(abs_row[index])),
                    }
                    for index in top_indices
                ],
            }
        )

    return {
        "prediction_shape": list(array.shape),
        "global_stats": {
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "global_mean": _clean_float(float(np.mean(finite))),
            "global_abs_mean": _clean_float(float(np.mean(np.abs(finite)))),
            "global_std": _clean_float(float(np.std(finite))),
            "global_min": _clean_float(float(np.min(finite))),
            "global_max": _clean_float(float(np.max(finite))),
        },
        "per_segment_stats": per_segment,
        "caution": (
            "Real TRIBE checkpoint output on synthetic resume-reading events; "
            "per-segment stats are compact summaries, not measured brain activity "
            "or hiring predictions."
        ),
    }


def save_prediction_or_summary(
    obj: Any,
    output_path: str,
    diagnostics_path: str,
    save_full_array: bool = False,
    full_array_path: str | None = None,
    segment_stats_path: str | None = None,
) -> dict:
    """Save a prediction as JSON when possible and always save diagnostics."""

    output = Path(output_path)
    diagnostics = Path(diagnostics_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    diagnostics.parent.mkdir(parents=True, exist_ok=True)
    full_array = Path(full_array_path) if full_array_path else output.with_suffix(".npz")
    segment_stats = Path(segment_stats_path) if segment_stats_path else None

    diagnostic_payload = {
        "serializable": False,
        "summary": summarize_object(obj),
        "output_path": str(output),
        "save_full_array": save_full_array,
    }
    if _is_numpy_array(obj):
        safe = _array_prediction_payload(obj)
        output.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")
        diagnostic_payload["serializable"] = True
        diagnostic_payload["prediction_shape"] = safe.get("prediction_shape")
        if segment_stats:
            stats_payload = compute_prediction_segment_stats(obj)
            segment_stats.parent.mkdir(parents=True, exist_ok=True)
            segment_stats.write_text(
                json.dumps(stats_payload, indent=2) + "\n", encoding="utf-8"
            )
            diagnostic_payload["segment_stats_path"] = str(segment_stats)
        if save_full_array:
            import numpy as np

            full_array.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(full_array, prediction=obj)
            diagnostic_payload["full_array_path"] = str(full_array)
    else:
        try:
            safe = to_json_safe(obj)
            output.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")
            diagnostic_payload["serializable"] = True
        except Exception as exc:
            output.write_text(
                json.dumps(summarize_object(obj), indent=2) + "\n", encoding="utf-8"
            )
            diagnostic_payload["serialization_error"] = f"{type(exc).__name__}: {exc}"

    diagnostics.write_text(
        json.dumps(diagnostic_payload, indent=2) + "\n", encoding="utf-8"
    )
    return diagnostic_payload


def _array_prediction_payload(obj: Any) -> dict:
    summary = _array_summary(obj)
    stats = compute_prediction_segment_stats(obj)
    return {
        "type": summary.get("type"),
        "prediction_shape": stats["prediction_shape"],
        "shape": stats["prediction_shape"],
        "dtype": stats["global_stats"]["dtype"],
        "size": summary.get("size"),
        "global_stats": stats["global_stats"],
        "min": stats["global_stats"]["global_min"],
        "max": stats["global_stats"]["global_max"],
        "mean": stats["global_stats"]["global_mean"],
        "std": stats["global_stats"]["global_std"],
        "preview_rows": summary.get("preview", []),
        "preview": summary.get("preview", []),
        "caution": stats["caution"],
    }


def _is_numpy_array(obj: Any) -> bool:
    try:
        import numpy as np

        return isinstance(obj, np.ndarray)
    except Exception:
        return False


def _is_torch_tensor(obj: Any) -> bool:
    return (
        hasattr(obj, "detach")
        and hasattr(obj, "cpu")
        and hasattr(obj, "tolist")
        and hasattr(obj, "shape")
    )
