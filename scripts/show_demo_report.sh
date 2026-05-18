#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f docs/demo_report.md ]]; then
  cat docs/demo_report.md
elif [[ -f outputs/demo_report.md ]]; then
  cat outputs/demo_report.md
else
  echo "No demo report found. Expected docs/demo_report.md or outputs/demo_report.md." >&2
  exit 1
fi
