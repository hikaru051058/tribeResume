# TRIBE Resume Text-Stimulus Experiment

## Goal

This experiment tests whether a resume can be represented as a timed text stimulus. The output is not a resume score. It is a synthetic event timeline that may later be passed into TRIBE v2's text pipeline once model access is configured.

## Converting A Resume Into Artificial Reading Events

A resume can be converted into word-level events:

```text
Education -> word event
State -> word event
University -> word event
Built -> word event
backend -> word event
API -> word event
```

Each event includes:

- `word`
- `onset`
- `duration`
- `offset`
- `index`

Example:

```json
{
  "word": "FastAPI",
  "onset": 13.912,
  "duration": 0.313,
  "offset": 14.225,
  "index": 51
}
```

## Fake Reading Timestamps

The timestamps are synthetic. They approximate how a person might move through a resume at a configured reading speed.

The current implementation uses:

- A base reading speed, defaulting to 220 words per minute.
- A small duration increase for longer words.
- A small duration increase for dense technical tokens like `C++`, `FastAPI`, `Node.js`, or `PostgreSQL`.

This is not a cognitive model. It is a practical way to create stable, inspectable event timelines for local experiments.

## Why This Avoids Video And Audio Preprocessing

The Meta notebook demonstrates text and video inputs, but the text path converts text into speech and then transcribes it back into word timings. The video path extracts audio, transcribes speech, and extracts visual/audio features.

For resume experiments, that is unnecessary at the first stage. We already have text. Artificial word events let us avoid:

- Text-to-speech.
- Audio generation.
- WhisperX transcription.
- Video extraction.
- ffmpeg.
- uvx.

## Current Blockers

Full TRIBE text prediction is not ready yet because:

- `meta-llama/Llama-3.2-3B` is gated and requires Hugging Face access.
- No Hugging Face token is configured locally yet.
- `uvx` is missing, which blocks the notebook's transcription path.
- `ffmpeg` is missing, which blocks the notebook's video/audio preprocessing path.
- `./tribev2/best.ckpt` is only a Git LFS pointer and should not be loaded directly.

## What Works Locally

The following works:

```python
from tribev2.demo_utils import TribeModel
```

Model loading from the Hugging Face cache works:

```python
model = TribeModel.from_pretrained(
    "facebook/tribev2",
    cache_folder="./cache_probe",
    device="cpu",
)
```

The real `facebook/tribev2` checkpoint is available through the Hugging Face cache. The local `./tribev2/best.ckpt` file is not the real checkpoint.

## Future TRIBE-Compatible Event Shape

The current JSON event format is scaffold-friendly. A future adapter should convert it into a pandas DataFrame with columns closer to TRIBE's expected `Word` events:

```text
type = "Word"
text = word
context = surrounding resume text
start = onset
duration = duration
timeline = "resume"
subject = "default"
```

After gated LLaMA access is solved, this DataFrame can be tested with:

```python
preds, segments = model.predict(events_df)
```

