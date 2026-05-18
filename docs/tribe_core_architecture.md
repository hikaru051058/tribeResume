# TRIBE-Core Architecture

## Corrected Architecture

The core system is a document perception simulator, not primarily an Ollama resume checker.

```text
Resume file
-> parser
-> text/layout representation
-> artificial reading events
-> TRIBE v2 prediction
-> response feature extraction
-> perception hypothesis layer
-> Ollama explanation layer
-> suggestion report
```

## Layer Responsibilities

### Parser

The parser converts PDF, DOCX, Markdown, or TXT into text plus metadata and warnings. It does not perfectly understand visual layout.

### Text/Layout Representation

The system represents the resume as normalized text, sections, and eventually layout features. Current layout support is limited.

### Artificial Reading Events

The event layer turns resume text into timed word events. These events are a bridge into TRIBE-style stimulus modeling.

### TRIBE v2 Prediction

TRIBE v2 is the core experimental perception-simulation layer. It can produce predicted brain-response-like activity from text, audio, video, or document-like stimuli.

This should be described cautiously:

- Predicted response pattern.
- Experimental signal.
- Proxy signal.
- Perception hypothesis.

It should not be described as actual perception or actual recruiter decision-making.

### Response Feature Extraction

Feature extraction summarizes predicted response patterns into proxy features:

- Section salience.
- Response intensity.
- Cognitive-load proxy.
- Underemphasized sections.
- Dense or confusing sections.

### Perception Hypothesis Layer

The system converts response features into cautious hypotheses about how the document may land cognitively.

Example:

> The projects section may draw high attention but may also feel dense because response variability and word density are high.

### Ollama Explanation Layer

Ollama explains TRIBE-derived signals in human language and combines them with resume text evidence. Ollama is not the unique core of the system by itself, and it should not be framed as the primary judge.

### Suggestion Report

The primary output is a report that explains what the predicted response pattern may suggest and which sections the user should inspect. Suggestions are not automatic edits.

### Optional Editing Tools

Rewrite and patch tools are downstream experiments. They may help users act on a report, but they are not the main system. The core product is the perception simulation and interpretation workflow.

## Fusion Layer

TRIBE-derived perception hypotheses should not replace reviewer feedback. They should be fused with reviewer-agent critique to prioritize what to fix.

Fusion asks:

- Where does the perception proxy suggest salience, density, or underemphasis?
- Where do reviewer agents also identify weakness or credibility risk?
- Where do the signals disagree?
- Which sections should be inspected first?

The output is a prioritized set of suggestion targets. It should use cautious language, especially when the perception source is mock data.

Fusion does not prove actual perception, hiring outcome, or resume quality. It produces suggestion priorities from experimental perception signals plus semantic reviewer feedback.

## Why Ollama Alone Is Not The Product

Ollama alone can simulate reviewer personas, but that is close to a local resume checker. It may produce useful critique, but it does not provide a perception-simulation signal.

The unique product idea depends on adding a brain-response-inspired signal before interpretation.

## Why TRIBE Alone Is Not Enough

TRIBE v2 does not directly judge resumes. It does not know hiring criteria, admissions rubrics, or role-fit semantics.

TRIBE-derived signals need interpretation:

- What section may be salient?
- What section may be cognitively dense?
- What text evidence explains the signal?
- What edit would preserve evidence while improving perception?

## Unique Value

The unique value is the combination:

```text
brain-response-inspired signal + local evaluator explanation + suggestion reporting
```

TRIBE provides experimental perception signal. Ollama explains and operationalizes it as a report. Patch tools are optional downstream helpers for users who choose to edit.
