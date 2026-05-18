# Rewrite And Compare Loop

## Why Reviewing Alone Is Not Enough

A review tells the user what is working and what is weak. That is useful, but it does not complete the product loop. A resume-response simulator should also help the user produce a better draft and test whether the new version changes simulated reader response.

The practical loop is:

```text
Original resume
-> reviewer-agent feedback
-> conservative rewrite
-> reviewer-agent feedback on revised resume
-> before/after comparison
```

## Why The System Should Improve The Resume

The product is more useful when it moves from diagnosis to iteration:

- Identify weak or confusing signals.
- Rewrite bullets for clarity and scanability.
- Preserve truthful claims.
- Make ATS-readable structure easier to parse.
- Compare whether the revised version looks better to the same reviewers.

This is still simulated evaluator feedback. It does not predict real hiring outcomes.

## Why Broad Rewrites Can Weaken Technical Resumes

Strong technical resumes often depend on concrete proof: metrics, system names, dates, technical stacks, role titles, project names, dataset sizes, latency numbers, funding amounts, publication names, and quantified improvements.

A broad rewrite can make the document shorter and cleaner while accidentally removing the evidence that made it credible. For technical resumes, preserving proof is usually more important than making every line sound polished.

## Evidence-Preserving Rewrite Policy

Default rewrite behavior is surgical:

- Preserve all numbers and metrics.
- Preserve company and project names.
- Preserve dates and role titles.
- Preserve technical stacks unless only duplicate skill listings are simplified.
- Preserve publication names and named systems.
- Improve wording around evidence instead of deleting evidence.
- Explain every removed evidence item.

Metrics should be preserved because they are often the strongest support for engineering impact, AI/ML credibility, and reviewer confidence.

GPA should not be removed by default. It may be removed only when the user explicitly passes `--allow-remove-gpa`.

## Surgical Vs Full Mode

`surgical` mode is the default. It edits weak bullets only, mostly preserves structure, and treats concrete evidence as protected.

`full` mode allows broader restructuring, but it still cannot invent facts and must report any removed evidence. Use full mode only when the resume structure itself is a major problem.

## How The Rewrite Step Works

The rewrite script reads:

- The original resume text.
- The prior review summary.
- An optional target role.
- A local Ollama model, defaulting to `qwen3:14b`.

It writes:

- `outputs/revised_resume.txt`
- `outputs/resume_rewrite.json`

The JSON includes:

- Revised resume text.
- Major changes.
- Removed or simplified claims.
- Risks or assumptions.
- Preserved evidence.
- Removed evidence and reasons.
- Bullet-level before/after changes.
- Safety warnings.
- Rewrite confidence.

## Why The System Must Avoid Inventing Facts

Resume rewrites can become dangerous if they add unsupported specificity. The rewriter must not invent:

- Companies.
- Dates.
- Metrics.
- Awards.
- Schools.
- Titles.
- Technologies.
- Publications.

If a better bullet would require missing information, the system should put that in `risks_or_assumptions` instead of silently adding it.

## Before/After Comparison

The comparison step is currently rule-based. It does not call an LLM.

It compares:

- Clarity.
- Credibility.
- ATS readability.
- Remaining risks.
- Likely reader-response change.
- Final recommendation.

If original and revised review summaries exist, it also considers the rating delta between the two review passes.

## Commands

```bash
python src/run_ollama_review.py --profile balanced --input examples/resume_sample.txt --output-prefix original
python src/run_resume_rewrite.py --model qwen3:14b --target-role "AI backend engineer intern" --mode surgical
python src/run_ollama_review.py --profile balanced --input outputs/revised_resume.txt --output-prefix revised
python src/run_resume_compare.py
```

Full mode with explicit GPA removal permission:

```bash
python src/run_resume_rewrite.py --model qwen3:14b --target-role "AI backend engineer intern" --mode full --allow-remove-gpa
```

## Limitations

- Local models can still produce weak rewrites.
- JSON output may need validation and retries in a production version.
- The comparison module uses simple rules and should not be treated as a final quality measure.
- Better wording does not guarantee better hiring or admissions outcomes.
- Every rewritten claim should be manually verified before use.
