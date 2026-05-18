# Real TRIBE Probe

## Purpose

`run_real_tribe_probe.py` is a guarded diagnostic script for testing whether real TRIBE v2 predictions can be generated from artificial resume reading events.

It does not judge resume quality. It does not measure real brain activity. It does not predict hiring outcomes.

## Setup Requirements

TRIBE model loading previously worked with:

```python
from tribev2.demo_utils import TribeModel

model = TribeModel.from_pretrained(
    "facebook/tribev2",
    cache_folder="./cache_probe",
    device="cpu",
)
```

The text prediction path may still require:

- Hugging Face login.
- Access to gated model dependencies such as `meta-llama/Llama-3.2-3B`.
- Local TRIBE dependencies.
- `uvx` if the upstream text path invokes it.
- `ffmpeg` if audio/video paths are accidentally used.

## Dry Run

Use dry run first. It parses the document, builds artificial reading events, saves them, and does not load TRIBE.

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run
```

Dry run writes:

- `outputs/real_tribe_events.json`
- `outputs/real_tribe_probe_diagnostics.json`

## Real Probe

Only run this when you explicitly want to attempt a real model call:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --output outputs/real_tribe_prediction_raw.json
```

The script attempts:

```python
model.predict(events)
```

The current event format is experimental and may not match the real TRIBE text pipeline.

## Canonical Word Event Path

The official TRIBE demo path typically creates events through media/text helpers such as `TextToEvents`, TTS/audio processing, transcription, and `get_events_dataframe`.

The resume probe avoids the audio/video path and creates synthetic word events directly. The canonical mapping is:

| Synthetic field | Canonical TRIBE/neuralset field |
| --- | --- |
| `word` | `text` |
| `onset` | `start` |
| `duration` | `duration` |
| synthetic row | `type = "Word"` |
| generated index | `word_index` |
| fixed metadata | `timeline`, `subject`, `language` |

The canonical dry run attempts the TRIBE event-preparation pipeline:

```text
standardize_events
-> AddText
-> AddSentenceToWords
-> AddContextToWords
-> RemoveMissing
-> standardize_events(auto_fill=False)
```

The canonical path requires the spaCy model `en_core_web_lg`. Install it explicitly before canonical mode if it is not already present; the probe code guards against silent model downloads.

Run raw DataFrame dry run:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run \
  --event-format dataframe
```

Run canonical dry run:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --dry-run \
  --event-format canonical
```

This writes:

- `outputs/real_tribe_events_dataframe.csv`
- `outputs/real_tribe_events_canonical.csv` if canonical transforms succeed
- `outputs/real_tribe_probe_diagnostics.json`

This is still experimental and may not match TRIBE's training distribution. Synthetic resume-reading events are a probe input, not a validated neuroscience measurement.

## Outputs

- `outputs/real_tribe_events.json`: synthetic word events.
- `outputs/real_tribe_prediction_raw.json`: JSON-safe prediction output or structural summary.
- `outputs/real_tribe_probe_diagnostics.json`: model loading, prediction, environment, and serialization diagnostics.

## Expected Blockers

Common failures:

- Hugging Face gated repository access.
- Missing access to a gated LLaMA dependency.
- Missing `uvx`.
- Missing `ffmpeg`.
- Wrong artificial event schema.
- Non-serializable prediction output.

For Hugging Face gated-model errors:

- `401` usually means the token is missing, expired, or not being picked up.
- `403` with "not in the authorized list" usually means you are logged in, but the account has not been granted access to that specific gated model.

## Text Embedding Failure Debugging

If the probe reaches a log line like:

```text
Preparing extractor: text
Computing word embeddings
```

then the canonical event schema probably passed the first validation stage. The next likely blockers are:

- Hugging Face access to a gated text embedding model.
- Missing access to a LLaMA dependency.
- Missing tokenizer/model files in the local cache.
- Incompatible `transformers`, `huggingface_hub`, or `torch` versions.
- Device-specific model loading issues.

Inspect the text extractor configuration:

```bash
python src/inspect_tribe_text_extractor.py
```

Run the real probe with verbose diagnostics:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --event-format canonical \
  --cache-folder ./cache_probe \
  --device cpu \
  --feature-device cpu \
  --verbose-errors
```

`--verbose-errors` prints the traceback and environment metadata. It reports whether an HF token is present, but never prints the token value.

On Apple Silicon or CPU-only PyTorch builds, use `--feature-device cpu`. TRIBE's checkpoint config may still set feature extractors such as `text_feature.device` to `cuda`; the probe overrides feature extractor devices before prediction and records the changes in diagnostics.

If `hf_token_set` is true and the error is still `403`, visit the model page and request/accept access:

```text
https://huggingface.co/meta-llama/Llama-3.2-3B
```

## Experimental Text Model Override

If the canonical text model is gated, you can test an experimental substitute through `transformers`:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --event-format canonical \
  --cache-folder ./cache_probe \
  --device cpu \
  --output outputs/real_tribe_prediction_raw.json \
  --text-model-override unsloth/Llama-3.2-3B-Instruct \
  --verbose-errors
```

This patches `model.data.text_feature.model_name` after loading the TRIBE checkpoint.

Important: this is not canonical TRIBE v2. The checkpoint was configured for `meta-llama/Llama-3.2-3B`, so replacing the text embedding model may change the representation distribution even if hidden dimensions match. Treat any output as:

```text
TRIBE checkpoint with experimental text-model override
```

Do not describe it as official TRIBE v2 output.

## Reading Diagnostics

Diagnostics include:

- input document metadata
- event count and preview
- whether `uvx` and `ffmpeg` are present
- model loading status
- prediction summary if available
- likely causes when failures occur

## Interpretation Limits

Fake reading events are an experimental bridge from resume text to a stimulus timeline. Even if real TRIBE prediction succeeds, the output is still a proxy signal.

Do not describe the output as actual perception, real neuroscience measurement, resume quality, or hiring prediction.
