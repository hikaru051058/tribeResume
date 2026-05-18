# TRIBE v2 Role

## What TRIBE v2 Is Good At

TRIBE v2 is a multimodal brain encoding model. It predicts fMRI brain responses to naturalistic stimuli such as video, audio, and text. It is useful for in-silico neuroscience and stimulus-response experiments.

For this product, the useful analogy is:

> A resume can be treated as a stimulus that creates attention, salience, and cognitive-load effects in a reader.

That framing is now the core experimental perception layer. The current implementation maps resume text into synthetic Word/Text/Sentence events, runs or ingests TRIBE-style prediction output, and aggregates response proxies by section.

## What TRIBE V2 Is Not Good At

TRIBE v2 should not be treated as:

- A resume-quality model.
- A hiring judgment model.
- An admissions review model.
- A role-fit scorer.
- A credibility evaluator.
- A replacement for structured LLM agents.
- A model that knows what recruiters or managers should value.

It predicts brain-response-like signals, not employment outcomes.

## Why It Should Not Directly Judge Resumes

Resume judgment is semantic, contextual, and institutional. It depends on:

- Role requirements.
- Hiring market.
- Candidate seniority.
- Evidence quality.
- Technical specificity.
- Domain expectations.
- Reviewer incentives.
- Admissions or hiring rubrics.

TRIBE v2 does not model these criteria directly. A resume could be visually salient but professionally weak, or cognitively easy to read but poorly matched to the role.

## Possible Experimental Uses

The current implemented uses are:

- Synthetic resume-reading event generation.
- Real TRIBE v2 prediction on canonical text events.
- Compact per-segment prediction statistics.
- Timeline-to-section mapping.
- Section-level salience, position-normalized salience, cognitive-load proxy, and underemphasis proxy.
- Controlled variant experiments that preserve facts while changing wording.

### Attention And Salience

TRIBE v2-style analysis could estimate whether certain parts of a rendered document are likely to attract attention. This may help identify whether a resume's strongest signals are visually buried.

Example questions:

- Does the reader's attention land on the candidate's strongest projects?
- Are important technical terms hidden inside dense paragraphs?
- Does the layout make section hierarchy obvious?

### Visual-Text Response

A rendered resume can be treated as a document-like visual stimulus. An experiment could compare visual responses across versions.

Example:

- Version A has dense two-column formatting.
- Version B has clearer headings and fewer bullets.
- The system estimates which version has lower visual complexity and clearer salience.

### Cognitive Load

TRIBE v2-inspired features may help detect when a resume is too dense or confusing as a stimulus.

Potential signals:

- High text density.
- Long bullets.
- Too many technologies per line.
- Weak section boundaries.
- Inconsistent formatting.
- Overloaded visual hierarchy.

### Document Density

The system can compute deterministic density metrics without TRIBE v2:

- Words per page.
- Average bullet length.
- Number of sections.
- Number of technologies listed.
- Ratio of metrics to generic claims.
- Layout complexity.

TRIBE v2 should only be added if it improves beyond these cheaper baselines.

### Comparing Resume Versions As Stimuli

TRIBE v2-style experiments could compare versions as stimuli:

| Version | Experimental Question |
| --- | --- |
| A | Does the original produce high density and weak salience? |
| B | Does the rewritten version make the strongest signal easier to notice? |
| C | Does a target-role version reduce cognitive load for a specific reader? |

## Clear Warning

LLM agents, deterministic rules, and rubric scoring are better for semantic hiring or admissions judgment.

TRIBE v2 may be useful for optional research around attention, salience, cognitive load, and document perception. It should not decide whether a resume is great, good, mixed, weak, or bad.
