# Local Model Comparison

## Benchmark Summary

Local test on `examples/resume_sample.txt`:

| Model Setup | Final Rating | Avg Confidence | Runtime | Structural Issues |
| --- | --- | ---: | ---: | ---: |
| `llama3.1:8b` for all agents | Good | 0.73 | 117.89s | 0 |
| `qwen3:14b` for all agents | Mixed | 0.70 | 389.67s | 0 |

`llama3.1:8b` is fast enough but can be too positive. `qwen3:14b` gives more useful critique but is too slow for all six agents by default.

## Recommended Profiles

### Fast

Use for development and quick checks:

```bash
python src/run_ollama_review.py --profile fast
```

Routing:

```yaml
default_model: llama3.1:8b
```

### Balanced

Use as the default local review profile:

```bash
python src/run_ollama_review.py --profile balanced
```

Routing:

```yaml
technical_recruiter: llama3.1:8b
ats_parser: llama3.1:8b
graduate_admissions_reviewer: llama3.1:8b
engineering_manager: qwen3:14b
ai_ml_reviewer: qwen3:14b
skeptical_reviewer: qwen3:14b
```

### Deep

Use when quality matters more than runtime:

```bash
python src/run_ollama_review.py --profile deep
```

Routing:

```yaml
default_model: qwen3:14b
```

### Adaptive

Use when you want fast first-pass coverage with selective stronger critique:

```bash
python src/run_ollama_review.py --profile adaptive --target-role "AI backend engineer intern"
```

Adaptive starts with `llama3.1:8b` and escalates selected agents to `qwen3:14b` based on rating, confidence, evidence quality, generic feedback, and target-role keywords.

## Selected Agents

Run only the personas you need:

```bash
python src/run_ollama_review.py --profile balanced --agents skeptical_reviewer,engineering_manager
```

## Parallel Mode

Run selected agents concurrently:

```bash
python src/run_ollama_review.py --profile balanced --parallel
```

Parallel mode may reduce wall-clock time, but it can increase memory pressure and model contention on local hardware.

## Manual Override

Use one model for every selected agent:

```bash
python src/run_ollama_review.py --model llama3.1:8b
python src/run_ollama_review.py --model qwen3:14b
```
