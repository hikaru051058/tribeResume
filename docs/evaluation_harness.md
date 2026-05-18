# Evaluation Harness

## Why Evaluation Is Needed

The resume-response simulator should not only produce plausible feedback. It should produce feedback that is useful, consistent, and grounded in resume evidence.

The evaluation harness provides a repeatable way to test whether local Ollama reviewer agents:

- Return valid structured JSON.
- Use allowed ratings.
- Keep confidence values in range.
- Include evidence quotes.
- Avoid generic advice without support.
- Respond sensibly to known fake resume weaknesses.

This still does not prove the system predicts real hiring outcomes.

This harness evaluates the optional reviewer-agent layer, not the core TRIBE perception pipeline. For real TRIBE evaluation, use timeline analysis, mock-vs-real comparison, and controlled variant experiments.

## Fake Resume Cases

The suite includes four fake resumes in `examples/eval_resumes/`:

| Resume | What It Tests |
| --- | --- |
| `weak_resume.txt` | Vague bullets, missing metrics, unclear dates, weak skills. |
| `good_resume.txt` | Decent structure, clear experience, some metrics, remaining improvement areas. |
| `overclaimed_resume.txt` | Inflated claims, suspicious wording, weak credibility. |
| `ats_bad_resume.md` | Fancy Markdown formatting, unclear sections, ATS-unfriendly structure. |

Expected issues are stored in `examples/eval_expectations.yaml`.

## Output Quality Checks

The rule-based evaluator checks each review for:

- Required fields.
- Evidence quote presence.
- Confidence between 0 and 1.
- Valid rating: Great, Good, Mixed, Weak, Bad.
- Generic feedback phrases such as "tailor your resume", "add more metrics", or "improve clarity" when they appear without meaningful evidence.

These checks are intentionally simple. They catch structural and evidence-quality failures before deeper human evaluation.

## Commands

Run the full suite with Ollama:

```bash
python src/run_eval_suite.py --profile fast
python src/run_eval_suite.py --profile balanced
python src/run_eval_suite.py --profile deep
python src/run_eval_suite.py --profile adaptive
```

Evaluate existing outputs without calling Ollama:

```bash
python src/run_eval_suite.py --skip-ollama
```

Limit the number of cases:

```bash
python src/run_eval_suite.py --profile fast --limit 2
```

## Outputs

The suite writes per-resume outputs under:

```text
outputs/eval/{resume_name}/
```

Reports:

```text
outputs/eval/eval_report.json
outputs/eval/eval_report.md
```

## How To Interpret Failures

Failures usually mean one of three things:

- The model output did not follow the schema.
- The feedback was too generic.
- Evidence quotes were missing or too weak.

An eval failure does not necessarily mean the model is useless. It means the prompt, schema, model choice, or parser output should be inspected.

## Human Reviewer Labels Later

The next evaluation step should add human labels:

- Expected rating by persona.
- Expected strengths and weaknesses.
- Evidence quote correctness.
- Rewrite usefulness.
- False positive credibility flags.

Human labels would allow calibration beyond rule-based checks.

## Limits

The harness tests output quality and expected behavior on fake resumes. It does not prove real-world hiring prediction, admissions prediction, or recruiter behavior.

TRIBE v2 is the core experimental perception layer, but it is not part of semantic hiring judgment. Reviewer-agent evaluation and TRIBE perception evaluation should be reported separately.
