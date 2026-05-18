#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python src/run_full_perception_report.py \
  --input examples/resume_sample.txt \
  --target-role "AI backend engineer intern" \
  --model llama3.1:8b \
  --mock
