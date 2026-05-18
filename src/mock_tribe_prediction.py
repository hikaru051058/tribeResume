"""Generate mock TRIBE-like prediction data for development."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS_PATH = ROOT / "outputs" / "resume_events.json"
DEFAULT_OUTPUT_PATH = ROOT / "outputs" / "mock_tribe_prediction.json"


def build_mock_prediction(events: list[dict]) -> dict:
    """Create deterministic pseudo-response values from word events."""

    token_responses = []
    section_responses: dict[str, list[float]] = {}
    current_section = "intro"
    section_words = {"education", "experience", "projects", "skills", "publications"}

    for event in events:
        word = str(event.get("word", ""))
        normalized = word.lower().strip(":")
        if normalized in section_words:
            current_section = normalized
        length_component = min(len(word) / 14.0, 1.0)
        symbol_component = 0.2 if any(char in word for char in ["+", "/", "-", "_", "."]) else 0.0
        numeric_component = 0.25 if any(char.isdigit() for char in word) else 0.0
        wave = (math.sin(event.get("index", 0) * 0.7) + 1) * 0.1
        value = round(min(1.0, 0.2 + length_component * 0.35 + symbol_component + numeric_component + wave), 4)
        token_responses.append(
            {
                "index": event.get("index"),
                "word": word,
                "section": current_section,
                "onset": event.get("onset"),
                "duration": event.get("duration"),
                "response_value": value,
            }
        )
        section_responses.setdefault(current_section, []).append(value)

    sections = []
    for section, values in section_responses.items():
        sections.append(
            {
                "section": section,
                "mean_response": round(sum(values) / len(values), 4) if values else 0.0,
                "max_response": round(max(values), 4) if values else 0.0,
                "token_count": len(values),
            }
        )

    return {
        "metadata": {
            "mock": True,
            "not_real_tribe_output": True,
            "description": "Deterministic pseudo-response data for downstream development only.",
        },
        "token_responses": token_responses,
        "section_responses": sections,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock TRIBE-like prediction JSON.")
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    events_path = Path(args.events)
    output_path = Path(args.output)
    events = json.loads(events_path.read_text(encoding="utf-8"))
    prediction = build_mock_prediction(events)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(prediction, indent=2) + "\n", encoding="utf-8")
    print(f"Saved mock prediction: {output_path}")


if __name__ == "__main__":
    main()

