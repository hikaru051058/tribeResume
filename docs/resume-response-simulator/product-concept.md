# Product Concept

## Core Idea

The current product is a TRIBE-inspired document perception simulator. It estimates how a resume or professional document may land as a timed stimulus before the user sends it.

The product flow:

```text
Resume/document upload
-> Parse text and section boundaries
-> Build synthetic reading events
-> Run real TRIBE v2 prediction or mock development signal
-> Save per-segment statistics
-> Map response segments to sections
-> Extract salience/load/underemphasis proxy features
-> Interpret proxy signals with evidence phrases
-> Produce suggestion priorities
-> Optionally compare with reviewer agents or controlled variants
```

## Reader-Response Simulator Framing

A resume is not just a data file. It is a stimulus shown to a reader under time pressure. The first-pass response often determines whether the document gets deeper attention.

The core product treats the resume as a stimulus first. Reviewer-agent personas remain useful as optional semantic comparison:

| Reader | Typical Question |
| --- | --- |
| Technical recruiter | Is this person plausibly qualified and worth screening? |
| Engineering manager | Can this person do the work on my team? |
| AI/ML reviewer | Are the ML claims technically real? |
| Graduate admissions reviewer | Does this show research promise and academic fit? |
| Skeptical reviewer | What sounds inflated or unsupported? |
| ATS parser | Can structured systems extract the right fields? |
| Startup founder | Can this person move fast and own ambiguous work? |
| Non-technical HR reader | Is the story understandable and professional? |

## Why Normal Resume Checkers Are Weak

Normal resume checkers often do one of three things:

- Keyword matching against a job description.
- Generic formatting and grammar feedback.
- Broad LLM advice that sounds helpful but is not calibrated to a real evaluator.

Common weaknesses:

- They over-index on keywords.
- They do not simulate different reader types.
- They do not cite exact evidence for judgments.
- They rarely distinguish credible strength from inflated language.
- They cannot explain why one version creates a stronger first impression than another.
- They do not track disagreement between reviewers.
- They often produce advice that is reasonable but generic.

## Why Perception Proxy Signals Are Useful

A candidate does not only need to know whether a bullet is "good." They need to know where the document may draw attention, where it may become dense, and whether important evidence may be buried.

Examples:

- A section with high raw salience may dominate the first-pass signal.
- A section with high position-normalized salience may remain prominent even after reducing early-section bias.
- A section with high cognitive-load proxy may be dense, long, or hard to scan.
- A section with high underemphasis proxy may contain strong evidence that is not surfacing clearly.
- A controlled variant can test whether clearer wording changes proxy signals while preserving facts.

The system is useful when it explains:

- What the raw TRIBE-style output represents.
- Which section-level proxy values drove each suggestion.
- Which evidence phrases came from the resume section.
- What cannot be concluded from the signal.
- Which optional reviewer-agent findings agree or disagree.

## Example Output

```json
{
  "metadata": {
    "perception_source": "real_tribe",
    "caution": "Real TRIBE checkpoint output from synthetic resume-reading events; no human was scanned."
  },
  "section_level_signals": [
    {
      "section": "experience",
      "salience_proxy": 0.71,
      "position_normalized_salience": 0.84,
      "cognitive_load_proxy": 0.92,
      "evidence_phrases": ["130,000+ reports", "~30% workload reduction", "3.4s inference latency"],
      "suggestion": "Inspect whether the experience section packs too many metrics and technologies into single spans."
    }
  ],
  "suggestion_priorities": [
    {
      "priority": 1,
      "section": "experience",
      "reasoning": "Highest cognitive-load proxy plus dense technical evidence."
    }
  ]
}
```

## Report Language

Reports should use cautious terms:

- "may suggest"
- "proxy signal"
- "perception hypothesis"
- "predicted response pattern"
- "inspect this section"

Reports should not say:

- "this predicts hiring outcomes"
- "this proves recruiter perception"
- "this is measured brain activity"
- "this section is objectively good or bad"
