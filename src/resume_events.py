"""Utilities for representing resume text as artificial reading events.

These helpers do not call TRIBE v2 directly. They create a lightweight
word-event representation that can later be adapted into the DataFrame shape
expected by TRIBE's text feature pipeline.
"""

from __future__ import annotations

import json
import re
import importlib.util
from pathlib import Path

import pandas as pd


def normalize_resume_text(text: str) -> str:
    """Normalize resume text while preserving readable word order."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_resume_into_words(text: str) -> list[str]:
    """Split normalized resume text into words and section-like tokens."""

    normalized = normalize_resume_text(text)
    if not normalized:
        return []
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9+#./'_-]*", normalized)


def estimate_word_duration(word: str) -> float:
    """Estimate how long a reader spends on one word, in seconds.

    This is intentionally simple. Longer and denser tokens receive a small
    duration increase to approximate extra reading effort.
    """

    clean_word = word.strip()
    if not clean_word:
        return 0.0

    length_penalty = max(len(clean_word) - 6, 0) * 0.015
    symbol_penalty = 0.04 if re.search(r"[+#./_-]", clean_word) else 0.0
    return round(0.20 + length_penalty + symbol_penalty, 3)


def build_fake_word_events(
    text: str, start_time: float = 0.0, base_wpm: int = 220
) -> list[dict]:
    """Convert resume text into artificial word events.

    The event timing is synthetic. It estimates a reading timeline from a base
    words-per-minute rate plus per-word duration adjustments.
    """

    if base_wpm <= 0:
        raise ValueError("base_wpm must be greater than 0")

    words = split_resume_into_words(text)
    base_duration = 60.0 / base_wpm
    onset = float(start_time)
    events: list[dict] = []

    for index, word in enumerate(words):
        duration = max(base_duration, estimate_word_duration(word))
        duration = round(duration, 3)
        offset = round(onset + duration, 3)
        events.append(
            {
                "word": word,
                "onset": round(onset, 3),
                "duration": duration,
                "offset": offset,
                "index": index,
            }
        )
        onset = offset

    return events


def save_events_json(events: list[dict], path: str) -> None:
    """Save artificial word events as pretty-printed JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")


def build_fake_word_events_dataframe(
    text: str,
    start_time: float = 0.0,
    base_wpm: int = 220,
    timeline: str = "resume",
    subject: str = "default",
    language: str = "en",
) -> pd.DataFrame:
    """Build canonical TRIBE-style word events as a pandas DataFrame."""

    rows = []
    for event in build_fake_word_events(text, start_time=start_time, base_wpm=base_wpm):
        rows.append(
            {
                "type": "Word",
                "text": event["word"],
                "start": event["onset"],
                "duration": event["duration"],
                "timeline": timeline,
                "subject": subject,
                "language": language,
                "word_index": event["index"],
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "type",
            "text",
            "start",
            "duration",
            "timeline",
            "subject",
            "language",
            "word_index",
        ],
    )


def prepare_tribe_word_events_dataframe(events_df: pd.DataFrame) -> pd.DataFrame:
    """Run TRIBE/neuralset event transforms on synthetic word events."""

    if importlib.util.find_spec("en_core_web_lg") is None:
        raise RuntimeError(
            "Canonical TRIBE text transforms require spaCy model en_core_web_lg. "
            "Install it explicitly before running canonical mode to avoid implicit downloads."
        )

    try:
        from tribev2.demo_utils import (
            AddContextToWords,
            AddSentenceToWords,
            AddText,
            RemoveMissing,
            standardize_events,
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not import TRIBE event transforms from tribev2.demo_utils."
        ) from exc

    events = events_df.copy()
    try:
        events = standardize_events(events)
        events = _run_events_transform(AddText(), events)
        events = _run_events_transform(
            AddSentenceToWords(max_unmatched_ratio=0.05), events
        )
        events = _run_events_transform(
            AddContextToWords(
                sentence_only=False,
                max_context_len=1024,
                split_field="",
            ),
            events,
        )
        events = _run_events_transform(RemoveMissing(), events)
        events = standardize_events(events, auto_fill=False)
    except Exception as exc:
        partial_path = Path("outputs") / "real_tribe_events_canonical_partial_failed.csv"
        partial_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            events.to_csv(partial_path, index=False)
        except Exception:
            pass
        raise RuntimeError(
            f"Failed while preparing canonical TRIBE events. Partial DataFrame saved to {partial_path}."
        ) from exc
    return events


def _run_events_transform(transform: object, events: pd.DataFrame) -> pd.DataFrame:
    """Run a neuralset transform regardless of its local method name."""

    if hasattr(transform, "run"):
        return transform.run(events)
    if hasattr(transform, "transform"):
        return transform.transform(events)
    if callable(transform):
        return transform(events)
    raise TypeError(f"Unsupported events transform API: {type(transform).__name__}")
