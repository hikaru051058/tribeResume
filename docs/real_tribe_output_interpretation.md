# Real TRIBE Output Interpretation

## What The Prediction Shape Means

The successful sample probe produced:

```text
(50, 20484)
```

This means:

- `50`: retained time/TR-like prediction segments.
- `20484`: predicted brain-response dimensions for each segment.

The second dimension likely corresponds to the target neural response vector used by the TRIBE checkpoint. It should be treated as a high-dimensional predicted response space, not as directly readable resume feedback.

In product terms, the raw output shape is:

```text
(n_segments, n_vertices_or_response_dimensions)
```

For the current sample:

```text
n_segments = 50
n_vertices_or_response_dimensions = 20,484
```

Those 20,484 dimensions are not resume labels. They are the cortical-surface-like output dimensions predicted by the checkpoint.

## Segment-Level Response Stats

The timeline analysis layer computes per-segment proxy statistics:

- `response_mean`
- `response_abs_mean`
- `response_std`
- `response_min`
- `response_max`

When `run_real_tribe_probe.py` succeeds, the serializer now saves compact exact per-segment statistics for every retained segment by default. Timeline analysis should use `--segment-stats` so it does not need the full prediction array and does not fall back to preview/global approximations.

`response_abs_mean` is used as a response-intensity proxy because it summarizes magnitude regardless of positive or negative direction in the predicted response vector.

## Why We Save Per-Segment Statistics

Full TRIBE prediction arrays can be large. The sample prediction is:

```text
(50, 20484)
```

That is manageable for a sample resume, but longer documents or richer outputs can grow quickly. The default probe therefore saves compact per-segment statistics instead of dumping the full array:

- segment-level mean
- absolute mean
- standard deviation
- min/max
- L2 norm
- positive/negative fraction
- top absolute response-value preview

These compact stats preserve the useful signal needed for timeline and section analysis without making the JSON output huge.

The full array can still be saved explicitly as compressed `.npz` when needed:

```bash
python src/run_real_tribe_probe.py \
  --input path/to/resume.pdf \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix sample \
  --save-full-array
```

Even with exact per-segment stats, section-level interpretation remains a proxy. It is still real TRIBE checkpoint output from synthetic reading events, not measured brain activity.

## Prefix-Safe Output Files

Real TRIBE runs should use `--output-prefix` to avoid mixing sample outputs with full-resume outputs:

```bash
python src/run_real_tribe_probe.py \
  --input examples/resume_sample.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --event-format canonical \
  --output-prefix sample
```

This writes:

- `outputs/sample_real_tribe_prediction_raw.json`
- `outputs/sample_real_tribe_segment_stats.json`
- `outputs/sample_real_tribe_segments_summary.json`
- `outputs/sample_real_tribe_events.json`
- `outputs/sample_real_tribe_events_dataframe.csv`
- `outputs/sample_real_tribe_events_canonical.csv`
- `outputs/sample_real_tribe_probe_diagnostics.json`

Timeline analysis should then use matching prefixed files:

```bash
python src/run_tribe_timeline_analysis.py \
  --input examples/resume_sample.txt \
  --prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --segment-stats outputs/sample_real_tribe_segment_stats.json \
  --events outputs/sample_real_tribe_events_canonical.csv \
  --output outputs/sample_tribe_timeline_analysis.json
```

## Deterministic Insights

The perception report now includes deterministic signal insights in addition to LLM interpretation.

These insights are generated directly from proxy rankings:

- highest `salience_proxy`
- highest `cognitive_load_proxy`
- highest `underemphasis_proxy`

This reduces overreliance on generic LLM phrasing. For example, if `projects` has the highest `cognitive_load_proxy`, the deterministic suggestion says to inspect whether project bullets are dense, long, or combining too many metrics and technologies in one span.

The deterministic insight is still a proxy interpretation. It should guide inspection, not claim a real reader response.

## Position Bias And Normalized Salience

Synthetic resume-reading events are sequential. Sections near the beginning of the document, such as contact, education, or coursework, may show high raw salience partly because they occur early in the constructed timeline.

This is a position effect risk. It should be visible in reports so users do not overinterpret early-section salience as proof that those sections are intrinsically more meaningful.

The pipeline therefore reports both:

- `salience_proxy`: raw section salience from response-intensity aggregation.
- `position_normalized_salience`: a simple heuristic that reduces early-section dominance based on section order.

The normalized value is not a TRIBE-native neuroscience metric. It is a transparent product heuristic for comparing raw salience against a position-adjusted view.

Interpretation guidance:

- If raw salience is highest in `intro` or `education`, check whether this may be an early-position effect.
- If normalized salience shifts to `experience`, `projects`, `publications`, or `skills`, inspect that section as a possible substantive signal.
- If both raw and normalized salience point to the same section, the section may be worth inspecting, but this still does not prove real reader attention.
- Use normalized salience together with cognitive-load and underemphasis proxies, not as a replacement for them.

## Controlled Variant Experiments

One-off interpretation is useful for inspection, but controlled variants are better for testing whether the proxy pipeline is sensitive to wording changes.

A controlled variant experiment keeps the same factual evidence while changing only the wording or structure. For example:

- Variant A: one dense SEM Medical Solutions bullet with many metrics and technologies in one sentence.
- Variant B: the same facts split into clearer bullets.

Facts must be preserved across variants:

- Dockerized AI-assisted medical reporting platform
- Elasticsearch semantic retrieval
- Bedrock-backed inference
- 130,000+ reports
- ~30% workload reduction
- ~2 hours saved
- ~6 to ~1 re-report corrections
- ~3.4s inference latency

The comparison checks whether section-level proxy values change:

- response intensity
- raw salience
- position-normalized salience
- cognitive-load proxy
- underemphasis proxy

What can be concluded:

- whether the proxy pipeline is sensitive to this controlled wording change
- whether the clearer variant reduces or increases a section-level load signal
- whether salience shifts between variants

What cannot be concluded:

- that one resume will perform better
- that real recruiters will respond differently
- that TRIBE validates a hiring outcome
- that lower proxy load is automatically better

Run a dry plan first:

```bash
python src/run_variant_experiment.py \
  --variant-a examples/variant_experiments/dense_sem_bullet.txt \
  --variant-b examples/variant_experiments/clear_sem_bullet.txt \
  --cache-folder ./cache_probe \
  --device cpu \
  --target-role "AI backend engineer intern" \
  --output-prefix sem_variant \
  --dry-run
```

## Variant Comparison Stability

Variant comparisons should be interpreted with section stability in mind.

Compare each section by:

- retained segment count
- section duration in the synthetic reading timeline
- cognitive-load proxy
- load per segment
- load per word when word count is available

Short sections can produce unstable load shifts because a small number of retained segments controls the section average. Segment boundaries also matter: splitting one dense bullet into multiple clearer bullets may change where section boundaries and segment overlaps fall in the synthetic timeline.

Facts preserved does not mean the perception proxy improved. It only means the comparison is better controlled.

Proxy improvement is directional evidence only:

- A lower load proxy in the target section may suggest clearer wording reduced density.
- A sharp increase in another short section may mean the signal shifted rather than cleanly improved.
- Large changes in sections with fewer than three segments, or substantially different durations, should be inspected in the timeline report before drawing conclusions.

## Mapping Segments To Resume Sections

TRIBE segments are mapped back to resume sections by time overlap:

```text
synthetic word timings -> section windows -> TRIBE segment times -> mapped section
```

For example, if the `Projects` section spans synthetic time `22s` to `34s`, any retained segment whose time overlaps that window is assigned to `Projects`.

The section summary then aggregates segment stats:

- average response intensity
- response variance
- maximum segment intensity
- segment count
- salience/load proxy values

This is useful for inspection, but it is still a proxy. Section aggregation is not a native TRIBE label and should not be interpreted as a direct cognitive measurement.

## Section-Level Aggregation

The perception-report pipeline aligns retained prediction segments to synthetic resume-reading section windows by time.

Example:

```text
resume section window: 15s -> 30s
TRIBE retained segments: 15s, 16s, 17s, ...
section feature: aggregate those segment-level prediction summaries
```

The current saved prediction file stores summary statistics and preview rows rather than the full raw array. When full segment arrays are unavailable, the adapter uses available global stats and preview-derived segment intensity where possible.

## Proxy Features

The report derives section-level proxy values:

- `response_intensity`: estimated magnitude of predicted response for aligned segments.
- `response_variance`: available variability proxy from saved prediction stats or preview rows.
- `salience_proxy`: normalized response intensity across sections.
- `cognitive_load_proxy`: combines response variance and section density.
- `underemphasis_proxy`: flags lower-salience sections that appear to contain concrete evidence.

These are product-level aggregation features. They are not native TRIBE labels.

## Why This Is A Proxy

The input is a synthetic resume-reading timeline, not natural reading or a real fMRI experiment.

The model output is real TRIBE checkpoint output, but the stimulus representation is artificial:

- words are assigned synthetic timestamps
- layout is mostly reduced to text order
- no human subject was scanned
- no actual recruiter perception was measured

The Meta demo workflow is built around naturalistic timed stimuli such as video, audio, and text events, then extracts modality features before prediction. The resume workflow currently uses synthetic text timings only. That means it exercises the TRIBE text path, but it may differ from natural reading, audio, and video conditions used by the demo and training setup.

## What Can Be Concluded

You can cautiously say:

- the real TRIBE checkpoint accepted the synthetic text-event pathway
- the output can be aggregated into section-level response-pattern hypotheses
- some sections may have higher or lower proxy salience than others

## What Cannot Be Concluded

Do not claim:

- the output measures actual brain activity
- the output predicts hiring outcomes
- TRIBE judges resume quality
- section salience means a real recruiter will focus there
- high cognitive-load proxy proves confusion

## Comparing Mock And Real Perception Signals

Mock perception features and real TRIBE-derived features can now be compared section by section:

```bash
python src/run_tribe_perception_probe.py \
  --input examples/resume_sample.txt \
  --mock \
  --output-prefix sample_mock

python src/run_tribe_perception_probe.py \
  --input examples/resume_sample.txt \
  --real-prediction outputs/sample_real_tribe_prediction_raw.json \
  --segments outputs/sample_real_tribe_segments_summary.json \
  --timeline-analysis outputs/sample_tribe_timeline_analysis.json \
  --output-prefix sample_real

python src/compare_perception_sources.py \
  --mock-features outputs/sample_mock_tribe_perception_features.json \
  --real-features outputs/sample_real_tribe_perception_features.json \
  --output outputs/perception_source_comparison.json
```

The initial sample comparison showed mixed agreement:

- shared sections: `6`
- major agreements: `9`
- major disagreements: `9`

That result means mock mode is useful for UI, report, and pipeline development, but it should not be treated as a meaningful substitute for real TRIBE output.

The comparison report ranks shared sections by:

- `salience_proxy`
- `cognitive_load_proxy`
- `underemphasis_proxy`

Agreement means the mock heuristic and real TRIBE-derived aggregation rank a section similarly for a proxy value. It should be treated as an inspection cue only, not validation.

Disagreement means the mock heuristic and real TRIBE-derived aggregation emphasize different sections. This may come from different assumptions, section timing alignment, synthetic reading events, or limitations in the saved prediction summary.

Mock should not be used as a substitute for real TRIBE. Real TRIBE output should be inspected and reported separately, with source metadata and cautions visible in every report.

This comparison does not validate mock signals, does not prove the real TRIBE aggregation is perceptually correct, and does not support hiring-outcome prediction.
