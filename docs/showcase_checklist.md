# Showcase Checklist

Use this checklist before sharing or pushing a public demo.

## Safe To Commit

- Source files under `src/`.
- Sanitized docs under `docs/`.
- Sanitized examples under `examples/`.
- Small helper scripts under `scripts/`.
- `outputs/.gitkeep`.

## Do Not Commit

- Real resumes or private documents.
- Generated `outputs/` files other than `.gitkeep`.
- Full TRIBE prediction arrays such as `*.npz`.
- Raw prediction summaries, segment stats, segment pickles, event CSVs, or probe diagnostics.
- Local model caches such as `cache_probe/`.
- Hugging Face tokens, `.env` files, or local credentials.
- Generated visualization HTML/PNG files if they contain private resume context.

## Pre-Push Checks

```bash
python -m py_compile src/*.py
git diff --check
git status --short
git ls-files | rg '(^outputs/|\\.npz$|segments\\.pkl|\\.env|cache_probe|\\.ckpt)' || true
```

## Demo Commands

Mock-only report:

```bash
bash scripts/demo_mock.sh
```

Existing-output visual dashboard:

```bash
python src/generate_visual_report.py \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --features outputs/hikaru_real_position_tribe_perception_features.json \
  --variant-comparison outputs/variant_experiments/sem_variant/variant_comparison.json \
  --output-dir outputs/visualizations
```

Real 3D mesh viewer from existing full prediction output:

```bash
python src/build_brain_mesh_viewer.py \
  --prediction-full outputs/hikaru_real_tribe_prediction_full.npz \
  --timeline outputs/hikaru_tribe_timeline_analysis.json \
  --events outputs/hikaru_real_tribe_events_canonical.csv \
  --section experience \
  --section-window peak \
  --n-timesteps 15 \
  --value-mode absolute \
  --colorscale activity \
  --output outputs/visualizations/brain_mesh_3d_viewer.html
```

## Public Framing

Use cautious language:

- real TRIBE checkpoint output from synthetic reading events
- proxy signal
- perception hypothesis
- not a real brain scan
- not a hiring prediction
- not proof of resume quality
