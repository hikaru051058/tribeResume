# Performance Tuning

## Local Benchmark Results

Measured on the local fake sample resume with six reviewer agents:

| Profile / Model | Final Rating | Avg Confidence | Runtime | Structural Issues |
| --- | --- | ---: | ---: | ---: |
| `llama3.1:8b` fast profile | Good | 0.73 | 117.89s | 0 |
| `qwen3:14b` all agents | Mixed | 0.70 | 389.67s | 0 |

`qwen3:14b` gives more useful critique, but it is too slow to run for every reviewer by default.

## Recommended Profiles

`fast` uses `llama3.1:8b` for every agent:

```bash
python src/run_ollama_review.py --profile fast
```

`balanced` uses `llama3.1:8b` for recruiter, ATS, and admissions review, then `qwen3:14b` for engineering manager, AI/ML reviewer, and skeptical reviewer:

```bash
python src/run_ollama_review.py --profile balanced
```

`deep` uses `qwen3:14b` for every agent:

```bash
python src/run_ollama_review.py --profile deep
```

`adaptive` starts with `llama3.1:8b`, then escalates selected agents to `qwen3:14b` only when needed:

```bash
python src/run_ollama_review.py --profile adaptive --target-role "AI backend engineer intern"
```

Escalation triggers:

- Any rating of Mixed, Weak, or Bad.
- Confidence below 0.70.
- Generic feedback.
- Missing evidence quotes.
- Skeptical reviewer always escalates.
- Engineering manager escalates for software/backend/AI/ML/data/systems/platform/engineer roles.
- AI/ML reviewer escalates for AI/ML/LLM/data science/NLP/computer vision/research roles.

Adaptive differs from `balanced` because it reacts to the first-pass output instead of preassigning specific agents to Qwen. Use it when you want better critique than `fast` but want to avoid the full cost of `deep`.

Risk: adaptive can still escalate many agents on weak resumes or technical target roles. Parallel adaptive mode may increase memory pressure.

## Selected Agents

Run only the agents you need:

```bash
python src/run_ollama_review.py --profile fast --agents technical_recruiter,ats_parser
python src/run_ollama_review.py --profile balanced --agents engineering_manager,ai_ml_reviewer,skeptical_reviewer
```

## Parallel Mode

Parallel mode runs selected agents concurrently:

```bash
python src/run_ollama_review.py --profile balanced --parallel
```

This may reduce wall-clock time, but it can increase memory pressure and model contention. Use default sequential mode if Ollama becomes unstable or the machine slows down.
