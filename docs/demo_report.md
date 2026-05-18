# TRIBE Resume Perception Demo Report

## One-Line Summary
A real TRIBE v2 checkpoint was used on synthetic resume-reading events to produce section-level perception proxy signals.

## Important Caution
- No human was scanned.
- The input was represented as synthetic reading events.
- This is not a hiring prediction.
- This is not proof of resume quality.
- Section-level aggregation is a product proxy, not a native TRIBE label.

## System Pipeline
```text
Resume PDF
-> canonical Word/Text/Sentence events
-> LLaMA 3.2 text features
-> TRIBE v2 prediction
-> per-segment stats
-> section mapping
-> perception report
```

## Real Full-Resume Run
- Prediction shape: `[182, 20484]`
- Retained segments: `182`
- Exact per-segment stats: `yes`
- Approximation used: `no`
- Highest raw salience section: `intro`
- Highest cognitive-load section: `experience`
- Highest underemphasis section: `experience`

Key interpretation:
- TRIBE's perception hypotheses suggest that certain sections may draw relatively high attention or be underemphasized relative to other sections.

## Controlled Variant Experiment
- Variant A: dense SEM-style bullet.
- Variant B: same facts split into clearer wording.
- Facts preserved: `True`
- Experience load delta: `-0.0654`
- Skills load spike warning: large change in a short section; inspect segment mapping

Interpretation:
- The clearer version reduced the proxy load signal for experience by 0.0654.

## What This Means
- The pipeline is sensitive to wording and structure changes in controlled variants.
- The full-resume experience section appears dense or high-load under the current proxy aggregation.
- Clearer wording may reduce the target-section load proxy.
- Stability warnings matter because signal can shift into short sections or segment-boundary artifacts.

## What This Does Not Mean
- It does not prove recruiters prefer one version.
- It does not measure actual perception.
- It does not validate resume quality.
- It does not replace human review.

## Next Steps
- Run more controlled variants with one change at a time.
- Improve section mapping and inspect segment-boundary behavior.
- Optionally add brain-surface visualization later.
- Compare proxy reports with human reviewer feedback.
