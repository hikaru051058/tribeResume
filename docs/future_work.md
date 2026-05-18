# Future Work

This project now has a working TRIBE-inspired document perception pipeline:

```text
document
-> synthetic reading events
-> real or mock TRIBE-style prediction
-> per-segment response statistics
-> section mapping
-> perception report
-> interactive visualization
```

The next work should focus on hardening, validation, and making the demo reproducible.

## Highest-Value Next Steps

1. Create one clean demo command.
   - Regenerate the showcase from existing outputs.
   - Include the dashboard, real 3D mesh viewer, timeline, section signals, variant comparison, and demo report.
   - Avoid rerunning TRIBE unless explicitly requested.

2. Keep the repository public-safe.
   - Do not commit real resumes, raw prediction arrays, `.npz` files, segment pickles, cache files, or generated visualization outputs.
   - Keep sanitized examples and docs in git.
   - Keep real local experiment outputs under ignored `outputs/`.

3. Strengthen mode warnings.
   - Mock mode should be visually marked as development/demo only.
   - Real TRIBE mode should be marked as real checkpoint output from synthetic reading events.
   - Reports should never imply hiring prediction, real measured perception, or real brain scans.

4. Improve section and time alignment.
   - Segment-to-section mapping is central to the product.
   - Improve word/event windows and section boundary logic.
   - Add diagnostics for segments near section boundaries.

5. Expand controlled variant experiments.
   - Dense vs clear SEM bullet is a useful first variant.
   - Add more one-change-at-a-time variants:
     - reordered sections
     - metric-heavy vs balanced bullet
     - grouped vs ungrouped skills
     - AI/ML detail added vs omitted
     - short vs long project descriptions

6. Add visual export documentation.
   - Explain how to generate the 3D mesh viewer.
   - Explain color modes and normalization.
   - Explain what the slider means.
   - Explain what not to conclude.

## Validation Work

- Compare TRIBE proxy shifts against human reviewer notes.
- Check whether controlled edits produce stable directionality across multiple resumes.
- Re-run the same document if any stochastic steps are introduced.
- Compare synthetic timing assumptions such as 180, 220, and 260 WPM.
- Track whether high cognitive-load proxy sections correspond to sections humans call dense or hard to scan.

## Product Polish

- Add a compact landing dashboard with `Run`, `Inspect`, `Compare`, and `Export` paths.
- Add section jump controls in the 3D viewer.
- Add a top-segments dropdown in the 3D viewer.
- Add screenshots or GIFs to docs.
- Add a sanitized public demo dataset.

## Core Caveat

The system is best framed as an experimental document perception simulator. It can show how a TRIBE-derived proxy signal changes across a synthetic reading timeline, but it does not prove actual reader perception, hiring outcomes, or resume quality.
