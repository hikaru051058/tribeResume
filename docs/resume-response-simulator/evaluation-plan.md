# Evaluation Plan

## Goal

The system is useful only if its simulated reactions help users make better document decisions. Evaluation should measure usefulness, calibration, evidence quality, and agreement with real reviewers.

## Human Reviewer Comparison

Collect reviews from real people matching target personas:

- Recruiters.
- Engineering managers.
- AI/ML reviewers.
- Admissions reviewers.
- Career coaches.

Compare:

- Overall response label.
- First impression.
- Top strengths.
- Top weaknesses.
- Credibility concerns.
- Role-fit score.

Metric:

```text
reviewer_agreement = matching_major_findings / total_major_findings
```

## A/B Resume Rewrite Testing

Test whether suggested rewrites improve human response.

Protocol:

1. Take original resume snippets.
2. Generate targeted rewrites.
3. Ask blinded reviewers to compare original vs rewritten version.
4. Record preference and reasons.

Metrics:

- Rewrite preference rate.
- Perceived clarity improvement.
- Perceived credibility improvement.
- Role-fit improvement.
- Rate of rewrites rejected as exaggerated or inaccurate.

## Agreement Between Agents And Real Reviewers

Evaluate each persona separately.

Example:

| Persona Agent | Human Comparison |
| --- | --- |
| Technical recruiter | Recruiter screen decision and keyword/fit notes. |
| Engineering manager | Manager notes on ownership, depth, and production impact. |
| AI/ML reviewer | Reviewer notes on technical credibility. |
| Skeptical reviewer | Human-identified inflated or unsupported claims. |
| ATS parser | Actual parser extraction results. |

## False Confidence Detection

The system must identify when it should be less certain.

Test cases:

- Poorly parsed PDFs.
- Vague claims with no evidence.
- Overloaded technical buzzwords.
- Missing dates or titles.
- Resume with impressive wording but weak substance.
- Resume with strong substance but bad formatting.

Metrics:

- Low-confidence recall.
- Unsupported claim detection rate.
- Hallucinated evidence rate.
- Missing-field detection accuracy.

## Calibration Of Response Labels

The labels Great, Good, Mixed, Weak, and Bad should map to reviewer behavior.

Possible calibration target:

| Label | Expected Human Pattern |
| --- | --- |
| Great | Most target reviewers would advance or strongly endorse. |
| Good | Many reviewers would advance with minor concerns. |
| Mixed | Reviewers disagree or need more evidence. |
| Weak | Most reviewers would not advance without major edits. |
| Bad | Document creates immediate rejection risk. |

## Metrics

### Reviewer Agreement

Measures whether simulated reactions match human reviewer reactions.

```text
agreement = aligned_labels_and_findings / total_compared_items
```

### Evidence Citation Accuracy

Measures whether cited lines actually support the judgment.

```text
citation_accuracy = valid_citations / total_citations
```

### Rewrite Usefulness

Measures whether rewrites improve the resume without adding unsupported claims.

```text
rewrite_usefulness = reviewer_preferred_rewrites / total_rewrites_reviewed
```

### Role-Match Improvement

Measures whether a targeted rewrite improves fit for a specific role.

```text
role_match_delta = rewritten_role_fit_score - original_role_fit_score
```

### Hallucination Rate

Measures invented facts or unsupported claims.

```text
hallucination_rate = unsupported_generated_claims / total_generated_claims
```

