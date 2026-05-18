# UI Flow

## Primary User Flow

1. Upload resume.
2. Choose target role and reader personas.
3. Optionally add a job description.
4. Run simulated reviewer analysis.
5. View first-pass reactions.
6. Inspect evidence-backed confidence.
7. Review rewrite suggestions.
8. Compare versions.

## Screen 1: Upload Resume

```text
+------------------------------------------------------+
| Resume Response Simulator                            |
+------------------------------------------------------+
| Upload resume                                        |
|                                                      |
| [ Drop PDF/DOCX/TXT here                         ]   |
|                                                      |
| Target role                                          |
| [ Backend Software Engineer                      ]   |
|                                                      |
| Optional job description                             |
| [ Paste job description...                       ]   |
|                                                      |
| Personas                                             |
| [x] Recruiter  [x] Engineering Manager  [x] ATS      |
| [ ] AI/ML Reviewer  [ ] Admissions  [x] Skeptical    |
|                                                      |
| [ Analyze Resume ]                                   |
+------------------------------------------------------+
```

## Screen 2: Simulated Reviewer Reactions

```text
+------------------------------------------------------+
| Overall Response: Mixed        Confidence: 76%        |
+------------------------------------------------------+
| 10-second first impression                            |
| Relevant backend experience, but impact and ownership |
| are under-specified for the target role.              |
+------------------------------------------------------+
| Persona reactions                                    |
|                                                      |
| Recruiter                 Good      80/100           |
| Engineering Manager       Mixed     68/100           |
| Skeptical Reviewer        Mixed     61/100           |
| ATS Parser                Good      84/100           |
+------------------------------------------------------+
```

## Screen 3: Evidence View

```text
+------------------------------------------------------+
| Strongest Signals                                    |
+------------------------------------------------------+
| Production backend experience                        |
| Evidence: line 22                                    |
| "Built REST APIs in Node.js and PostgreSQL..."       |
|                                                      |
| Clear technical stack                                |
| Evidence: lines 10-12                                |
+------------------------------------------------------+
| Weak Or Confusing Signals                            |
+------------------------------------------------------+
| Vague impact claim                                   |
| Evidence: line 25                                    |
| "Improved system performance and user experience"    |
|                                                      |
| Missing scale                                        |
| Evidence: no user count, traffic, team size, or SLA   |
+------------------------------------------------------+
```

## Screen 4: Confidence Breakdown

```text
+------------------------------------------------------+
| Confidence Breakdown                                 |
+------------------------------------------------------+
| Parser confidence              91%                   |
| Evidence coverage              84%                   |
| Rubric consistency             79%                   |
| Persona agreement              68%                   |
| Required fields                82%                   |
| Ambiguity score                70%                   |
| Supported claims               75%                   |
+------------------------------------------------------+
| Main reason confidence is not higher:                 |
| Several important claims lack metrics, scope, or      |
| ownership evidence.                                  |
+------------------------------------------------------+
```

## Screen 5: Rewrite Suggestions

```text
+------------------------------------------------------+
| Suggested Bullet Rewrite                             |
+------------------------------------------------------+
| Original                                             |
| Worked on APIs for onboarding.                       |
|                                                      |
| Rewrite                                              |
| Built and maintained onboarding REST APIs in Node.js  |
| and PostgreSQL, improving account setup reliability   |
| for customer support workflows.                      |
|                                                      |
| Why this helps                                       |
| Adds ownership, stack, and product context without    |
| inventing unsupported metrics.                       |
|                                                      |
| [ Accept ] [ Edit ] [ Regenerate ]                   |
+------------------------------------------------------+
```

## Screen 6: Version Comparison

```text
+------------------------------------------------------+
| Compare Resume Versions                              |
+------------------------------------------------------+
| Version A: Original                                  |
| Version B: Backend-targeted rewrite                  |
|                                                      |
| Overall winner: Version B                            |
|                                                      |
| Recruiter:              B                            |
| Engineering Manager:    B                            |
| Skeptical Reviewer:     A                            |
| ATS Parser:             B                            |
|                                                      |
| Tradeoff                                               |
| Version B is stronger and clearer, but one rewritten  |
| bullet may need user verification.                   |
+------------------------------------------------------+
```

## UI Principles

- Show persona disagreement instead of hiding it.
- Keep evidence visible near every judgment.
- Avoid pretending the system predicts hiring outcomes.
- Label confidence as evidence support, not certainty of success.
- Make rewrite risks visible when a suggestion adds specificity.

