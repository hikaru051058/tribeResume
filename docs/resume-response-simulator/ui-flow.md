# UI Flow

## Current Status

This is a product sketch for the current TRIBE-first perception-report system. Reviewer-agent screens and editing screens are optional downstream views, not the main workflow.

## Primary User Flow

1. Upload resume or professional document.
2. Choose target role or document context.
3. Choose perception source: mock demo or real TRIBE output.
4. Run perception probe and timeline analysis.
5. View section-level proxy rankings.
6. Inspect evidence-backed perception hypotheses.
7. Optionally compare with reviewer agents.
8. Optionally generate patch suggestions or compare controlled variants.

## Screen 1: Upload Resume

```text
+------------------------------------------------------+
| TRIBE Document Perception Report                     |
+------------------------------------------------------+
| Upload document                                      |
|                                                      |
| [ Drop PDF/DOCX/TXT/MD here                      ]   |
|                                                      |
| Target role                                          |
| [ AI backend engineer intern                     ]   |
|                                                      |
| Perception source                                    |
| [ ] Mock demo only  [x] Real TRIBE outputs            |
|                                                      |
| [ Generate Perception Report ]                       |
+------------------------------------------------------+
```

## Screen 2: Proxy Signal Rankings

```text
+------------------------------------------------------+
| EXPERIMENTAL REAL TRIBE MODE                         |
+------------------------------------------------------+
| Raw prediction shape: [182, 20484]                    |
| Retained segments: 182                                |
| Exact per-segment stats: yes                          |
| No human was scanned. Not a hiring prediction.        |
+------------------------------------------------------+
| Highest Salience                                     |
| 1 intro                         1.00                 |
| 2 education/coursework          0.88                 |
+------------------------------------------------------+
| Highest Cognitive Load Proxy                         |
| 1 experience                    0.91                 |
| 2 projects                      0.76                 |
+------------------------------------------------------+
```

## Screen 3: Section Signal Detail

```text
+------------------------------------------------------+
| Experience                                           |
+------------------------------------------------------+
| salience_proxy: 0.71                                  |
| position_normalized_salience: 0.84                    |
| cognitive_load_proxy: 0.91                            |
| underemphasis_proxy: 0.88                             |
|                                                      |
| Evidence phrases                                     |
| - 130,000+ medical reports                           |
| - ~30% workload reduction                            |
| - ~3.4s inference latency                            |
+------------------------------------------------------+
| Suggestion                                           |
| Because experience has the highest load proxy,        |
| inspect whether dense metrics and technologies can    |
| be split without removing evidence.                   |
+------------------------------------------------------+
```

## Optional Screen: Reviewer Comparison

```text
+------------------------------------------------------+
| Perception + Reviewer Fusion                         |
+------------------------------------------------------+
| Agreement                                             |
| - Experience: high load proxy and reviewer concern    |
|   about dense AI/backend evidence.                    |
|                                                      |
| Disagreement                                          |
| - Skills: lower TRIBE signal but reviewer finds       |
|   keyword coverage useful.                            |
+------------------------------------------------------+
```

## Optional Screen: Patch Suggestions

```text
+------------------------------------------------------+
| Suggested Bullet Patch                               |
+------------------------------------------------------+
| Original                                             |
| Built a dense technical system with metrics...        |
|                                                      |
| Proposed                                             |
| Split the same evidence into a more scannable span... |
|                                                      |
| Validation                                           |
| Risk: low                                            |
| Evidence preserved: yes                              |
| Cross-section evidence: none                          |
| Entity drift: none                                   |
+------------------------------------------------------+
```

## UI Principles

- Lead with source mode: mock demo or real TRIBE.
- Show no-human-scan and no-hiring-prediction warnings near the top.
- Show proxy values and rankings before interpretation text.
- Keep evidence phrases visible near every suggestion.
- Prefer "inspect this section" language over automatic edits.
- Keep reviewer agents, fusion, patching, and rewriting visually optional.
