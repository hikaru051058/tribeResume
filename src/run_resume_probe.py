"""Generate artificial resume reading events for local inspection.

This probe intentionally does not call TRIBE v2 prediction yet. The current
TRIBE text path depends on gated access to meta-llama/Llama-3.2-3B.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from resume_events import build_fake_word_events, save_events_json


ROOT = Path(__file__).resolve().parents[1]
RESUME_PATH = ROOT / "examples" / "resume_sample.txt"
OUTPUT_PATH = ROOT / "outputs" / "resume_events.json"
METADATA_PATH = ROOT / "outputs" / "resume_events_metadata.json"


def main() -> None:
    """Build fake resume events and print a compact summary."""

    parser = argparse.ArgumentParser(description="Generate fake resume word events.")
    parser.add_argument(
        "--input",
        default=str(RESUME_PATH),
        help="Path to resume document: .txt, .md, .docx, or text-based .pdf.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    parsed = parse_document(str(input_path))
    resume_text = parsed["text"]
    events = build_fake_word_events(resume_text)
    save_events_json(events, str(OUTPUT_PATH))
    METADATA_PATH.write_text(
        json.dumps(
            {
                "source_path": parsed["source_path"],
                "file_type": parsed["file_type"],
                "metadata": parsed["metadata"],
                "warnings": parsed["warnings"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    total_time = events[-1]["offset"] if events else 0.0

    print(f"Loaded resume: {input_path}")
    print(f"Detected file type: {parsed['file_type']}")
    print(f"Parsed word count: {parsed['metadata'].get('word_count', 0)}")
    if parsed["warnings"]:
        print("Warnings:")
        for warning in parsed["warnings"]:
            print(f"- {warning}")
    print(f"Saved events: {OUTPUT_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")
    print(f"Number of words: {len(events)}")
    print(f"Total simulated reading time: {total_time:.2f}s")
    print("First 10 events:")
    for event in events[:10]:
        print(event)

    # TODO:
    # Convert these events into a pandas DataFrame with TRIBE-compatible Word
    # event columns: type, text, context, start, duration, timeline, subject.
    # Then try:
    #   preds, segments = model.predict(events_df)
    # after Hugging Face access to meta-llama/Llama-3.2-3B is configured.


if __name__ == "__main__":
    main()
