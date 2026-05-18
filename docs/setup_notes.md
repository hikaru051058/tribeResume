# Setup Notes

## Current Local State

The `tribev2` Python package is installed locally from:

```text
/Users/hikaru/tribev2
```

This import works:

```python
from tribev2.demo_utils import TribeModel
```

This model load works:

```python
model = TribeModel.from_pretrained(
    "facebook/tribev2",
    cache_folder="./cache_probe",
    device="cpu",
)
```

Do not load `./tribev2/best.ckpt` directly. It is only a Git LFS pointer in this workspace.

## Required Setup For Full TRIBE Text Prediction

The current TRIBE text feature path requires access to the gated Hugging Face model:

```text
meta-llama/Llama-3.2-3B
```

Log in with:

```bash
huggingface-cli login
```

Then confirm your Hugging Face account has accepted access to `meta-llama/Llama-3.2-3B`.

## Setup Commands

Install ffmpeg for audio/video preprocessing:

```bash
brew install ffmpeg
```

Install Git LFS if you want local LFS-backed checkpoint files to materialize:

```bash
brew install git-lfs
```

Install `uv` / `uvx`, which TRIBE's WhisperX transcription path expects:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Notes

The current app path uses synthetic resume-reading events and the TRIBE text extractor. It does not require the notebook's audio/video/transcription path, but full real TRIBE text prediction still needs Hugging Face access to the configured LLaMA dependency.

Generated outputs and caches are ignored by git:

- `outputs/`
- `cache_probe/`
- local resume PDFs
- local notebooks
- local TRIBE checkouts

Keep real resumes and generated reports local unless they have been intentionally sanitized.
