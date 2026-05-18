# Meta TRIBE Demo Alignment

## Meta Demo Workflow

The Meta TRIBE v2 demo is organized around naturalistic stimuli and timed event streams:

- video, audio, and text stimuli
- timed events
- modality feature extraction
- LLaMA 3.2 text features
- V-JEPA2 video features
- Wav2Vec-BERT audio features
- TRIBE prediction
- cortical-surface-style output
- brain-response visualization

The demo is not a resume checker. It predicts brain-response-like activity from stimulus representations.

## Resume System Workflow

The resume perception system maps a resume into a timed text stimulus:

```text
resume/document
-> parser
-> synthetic reading events
-> canonical Word/Text/Sentence events
-> LLaMA 3.2 text features
-> TRIBE prediction
-> high-dimensional predicted response output
-> section-level aggregation
-> perception report
```

The successful sample path produced real TRIBE checkpoint output with shape:

```text
(50, 20484)
```

This means 50 retained time/TR-like segments and 20,484 predicted output dimensions.

## How The Mapping Works

| Meta Demo | Resume System |
| --- | --- |
| Naturalistic video/audio/text stimuli | Resume text treated as a synthetic timed text stimulus |
| Timed event dataframe | Canonical Word/Text/Sentence event dataframe |
| LLaMA 3.2 / V-JEPA2 / Wav2Vec-BERT features | LLaMA 3.2 text features only for now |
| TRIBE prediction | TRIBE prediction |
| Cortical-surface-like output | Cortical-surface-like output |
| Brain visualization | Section-level timeline and perception report |

## Important Differences

- No naturalistic video/audio is used unless added later.
- Resume reading timings are synthetic.
- No human response is measured.
- No recruiter perception is validated.
- No hiring outcome correlation is claimed.
- Document layout is mostly reduced to text order unless a visual/PDF image pathway is added later.

## Product Interpretation

The unique product layer is not the raw TRIBE prediction by itself. It is the translation from raw predicted response patterns into cautious document-inspection signals:

- segment response intensity
- section salience proxy
- cognitive-load proxy
- underemphasis proxy
- section-level interpretation
- suggestion priorities

These outputs should be described as perception hypotheses, not conclusions.
