"""Run local Ollama reviewer agents against the sample resume."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from adaptive_review import merge_adaptive_reviews, should_escalate_review
from aggregate_reviews import aggregate_review_results
from document_parser import parse_document
from model_routing import get_adaptive_config, load_model_routing, resolve_agent_model
from ollama_client import call_ollama_chat
from reviewer_agents import REVIEWER_AGENTS, ReviewerAgent
from reviewer_schemas import REVIEWER_OUTPUT_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
RESUME_PATH = ROOT / "examples" / "resume_sample.txt"
DEFAULT_OUTPUTS_DIR = ROOT / "outputs"


def resolve_output_paths(
    output_prefix: str | None, output_dir: str | Path = DEFAULT_OUTPUTS_DIR
) -> tuple[Path, Path]:
    """Resolve review and summary output paths."""

    outputs_dir = Path(output_dir)
    if not outputs_dir.is_absolute():
        outputs_dir = ROOT / outputs_dir
    if output_prefix:
        return (
            outputs_dir / f"{output_prefix}_ollama_reviews.json",
            outputs_dir / f"{output_prefix}_ollama_review_summary.json",
        )
    return (
        outputs_dir / "ollama_reviews.json",
        outputs_dir / "ollama_review_summary.json",
    )


def build_user_prompt(resume_text: str, agent: ReviewerAgent) -> str:
    """Build the user prompt for one reviewer persona."""

    return f"""Review this resume as: {agent.name}

Scoring focus:
{json.dumps(agent.scoring_focus, indent=2)}

Resume text:
---
{resume_text}
---

Return only JSON. Every major judgment must be supported by exact resume phrases in evidence_quotes.
If evidence is missing, say what is missing instead of inventing it."""


def run_agent(model: str, resume_text: str, agent: ReviewerAgent) -> dict:
    """Run one reviewer agent through Ollama."""

    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": build_user_prompt(resume_text, agent)},
    ]
    response = call_ollama_chat(
        model=model,
        messages=messages,
        temperature=0.2,
        format_schema=REVIEWER_OUTPUT_SCHEMA,
    )
    result = response["parsed"]
    if not isinstance(result, dict):
        result = {"raw_content": str(result)}
    result.setdefault("persona", agent.key)
    return result


def print_summary_table(results: list[dict]) -> None:
    """Print a readable persona summary table."""

    print("\npersona | model | rating | confidence | seconds | first impression")
    print("--- | --- | --- | --- | --- | ---")
    for result in results:
        persona = result.get("persona", "unknown")
        model = result.get("model", "unknown")
        rating = result.get("rating", "unknown")
        confidence = result.get("confidence", "unknown")
        if isinstance(confidence, int | float):
            confidence = f"{confidence:.2f}"
        elapsed = result.get("elapsed_seconds", "unknown")
        if isinstance(elapsed, int | float):
            elapsed = f"{elapsed:.2f}"
        first_impression = result.get("first_impression", "")
        if result.get("error"):
            first_impression = f"ERROR: {result['error']}"
        print(
            f"{persona} | {model} | {rating} | {confidence} | "
            f"{elapsed} | {first_impression}"
        )


def select_agents(agent_keys: str | None) -> list[ReviewerAgent]:
    """Select reviewer agents from a comma-separated key list."""

    if not agent_keys:
        return REVIEWER_AGENTS

    requested = [key.strip() for key in agent_keys.split(",") if key.strip()]
    by_key = {agent.key: agent for agent in REVIEWER_AGENTS}
    unknown = [key for key in requested if key not in by_key]
    if unknown:
        valid = ", ".join(sorted(by_key))
        raise ValueError(f"Unknown agent(s): {', '.join(unknown)}. Valid agents: {valid}")
    return [by_key[key] for key in requested]


def run_agent_with_metadata(
    model: str,
    resume_text: str,
    agent: ReviewerAgent,
    profile: str,
) -> dict:
    """Run one agent and preserve timing or error metadata."""

    agent_start = time.perf_counter()
    try:
        result = run_agent(model, resume_text, agent)
    except Exception as exc:
        result = {
            "persona": agent.key,
            "rating": "Bad",
            "confidence": 0.0,
            "first_impression": "",
            "strongest_signals": [],
            "weak_or_confusing_signals": [],
            "credibility_risks": [],
            "evidence_quotes": [],
            "suggested_fixes": [],
            "final_summary": "",
            "error": f"{type(exc).__name__}: {exc}",
        }
    elapsed_seconds = time.perf_counter() - agent_start
    result.setdefault("persona", agent.key)
    result["model"] = model
    result["routing_profile"] = profile
    result["elapsed_seconds"] = round(elapsed_seconds, 3)
    return result


def run_agents(
    agents: list[ReviewerAgent],
    agent_models: dict[str, str],
    resume_text: str,
    profile: str,
    parallel: bool,
) -> list[dict]:
    """Run a group of agents sequentially or concurrently."""

    if parallel and agents:
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            future_to_agent = {}
            for agent in agents:
                model = agent_models[agent.key]
                print(f"Running {agent.name} with {model}...")
                future = executor.submit(
                    run_agent_with_metadata, model, resume_text, agent, profile
                )
                future_to_agent[future] = agent
            result_by_key = {}
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result_by_key[agent.key] = future.result()
                except Exception as exc:
                    result_by_key[agent.key] = {
                        "persona": agent.key,
                        "model": agent_models[agent.key],
                        "routing_profile": profile,
                        "elapsed_seconds": 0.0,
                        "rating": "Bad",
                        "confidence": 0.0,
                        "first_impression": "",
                        "strongest_signals": [],
                        "weak_or_confusing_signals": [],
                        "credibility_risks": [],
                        "evidence_quotes": [],
                        "suggested_fixes": [],
                        "final_summary": "",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            return [result_by_key[agent.key] for agent in agents]

    results = []
    for agent in agents:
        model = agent_models[agent.key]
        print(f"Running {agent.name} with {model}...")
        results.append(run_agent_with_metadata(model, resume_text, agent, profile))
    return results


def run_review(
    input_path: str,
    profile: str,
    model_override: str | None,
    output_prefix: str | None,
    output_dir: str = "outputs",
    agent_keys: str | None = None,
    parallel: bool = False,
    target_role: str | None = None,
) -> dict:
    """Run reviewer agents and save review/summary JSON outputs."""

    resolved_input_path = Path(input_path)
    if not resolved_input_path.is_absolute():
        resolved_input_path = ROOT / resolved_input_path
    reviews_path, summary_path = resolve_output_paths(output_prefix, output_dir)

    parsed_document = parse_document(str(resolved_input_path))
    resume_text = parsed_document["text"]
    print(f"Input path: {resolved_input_path}")
    print(f"Detected file type: {parsed_document['file_type']}")
    print(f"Word count: {parsed_document['metadata'].get('word_count', 0)}")
    if parsed_document["warnings"]:
        print("Warnings:")
        for warning in parsed_document["warnings"]:
            print(f"- {warning}")

    reviews_path.parent.mkdir(parents=True, exist_ok=True)
    routing = load_model_routing()
    selected_agents = select_agents(agent_keys)

    results = []
    adaptive_metadata = None
    total_start = time.perf_counter()

    if profile == "adaptive" and not model_override:
        adaptive_config = get_adaptive_config(routing)
        first_pass_model = adaptive_config["first_pass_model"]
        escalation_model = adaptive_config["escalation_model"]

        first_pass_start = time.perf_counter()
        first_pass_models = {agent.key: first_pass_model for agent in selected_agents}
        first_pass_results = run_agents(
            selected_agents, first_pass_models, resume_text, profile, parallel
        )
        first_pass_runtime = time.perf_counter() - first_pass_start

        by_key = {agent.key: agent for agent in selected_agents}
        escalation_reasons = {}
        escalate_agents = []
        for review in first_pass_results:
            persona = review.get("persona")
            should_escalate, reasons = should_escalate_review(
                review, persona, target_role, adaptive_config
            )
            if should_escalate and persona in by_key:
                escalation_reasons[persona] = reasons
                escalate_agents.append(by_key[persona])
                review["escalation_reasons"] = reasons
                review["first_pass_model"] = first_pass_model

        escalation_start = time.perf_counter()
        escalation_models = {agent.key: escalation_model for agent in escalate_agents}
        escalated_results = run_agents(
            escalate_agents, escalation_models, resume_text, profile, parallel
        )
        escalation_runtime = time.perf_counter() - escalation_start

        for review in escalated_results:
            persona = review.get("persona")
            review["first_pass_model"] = first_pass_model
            review["escalated_model"] = escalation_model
            review["escalation_reasons"] = escalation_reasons.get(persona, [])
            review["was_escalated"] = True

        results = merge_adaptive_reviews(first_pass_results, escalated_results)
        for review in results:
            review.setdefault("first_pass_model", first_pass_model)
            review.setdefault("was_escalated", False)

        adaptive_metadata = {
            "first_pass_model": first_pass_model,
            "escalation_model": escalation_model,
            "first_pass_runtime_seconds": round(first_pass_runtime, 3),
            "escalation_runtime_seconds": round(escalation_runtime, 3),
            "escalated_agents": [agent.key for agent in escalate_agents],
            "escalation_reasons": escalation_reasons,
            "target_role": target_role,
        }
    else:
        agent_models = {
            agent.key: resolve_agent_model(
                profile_name=profile,
                agent_key=agent.key,
                manual_model=model_override,
                routing=routing,
            )
            for agent in selected_agents
        }
        results = run_agents(selected_agents, agent_models, resume_text, profile, parallel)

    total_runtime_seconds = time.perf_counter() - total_start
    aggregate = aggregate_review_results(results)
    aggregate["routing_profile"] = profile
    aggregate["manual_model_override"] = model_override
    aggregate["total_runtime_seconds"] = round(total_runtime_seconds, 3)
    aggregate["parallel"] = parallel
    aggregate["selected_agents"] = [agent.key for agent in selected_agents]
    aggregate["target_role"] = target_role
    if adaptive_metadata is not None:
        aggregate["adaptive"] = adaptive_metadata
    aggregate["final_aggregator_model"] = (
        model_override
        or routing.get(profile, {}).get("final_aggregator")
        or "deterministic_aggregate_reviews"
    )
    document_metadata = {
        "source_path": parsed_document["source_path"],
        "file_type": parsed_document["file_type"],
        "metadata": parsed_document["metadata"],
        "warnings": parsed_document["warnings"],
    }
    aggregate["document_metadata"] = document_metadata

    output_payload = {
        "document_metadata": document_metadata,
        "reviews": results,
    }
    if adaptive_metadata is not None:
        output_payload["adaptive"] = adaptive_metadata

    reviews_path.write_text(
        json.dumps(output_payload, indent=2) + "\n", encoding="utf-8"
    )
    summary_path.write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")

    return {
        "reviews": results,
        "summary": aggregate,
        "reviews_path": str(reviews_path),
        "summary_path": str(summary_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local Ollama resume reviewers.")
    parser.add_argument(
        "--profile",
        default="balanced",
        choices=["fast", "balanced", "deep", "adaptive"],
        help="Model routing profile from configs/model_routing.yaml.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Manual Ollama model override for all agents, such as qwen3:14b.",
    )
    parser.add_argument(
        "--input",
        default=str(RESUME_PATH),
        help="Path to resume document: .txt, .md, .docx, or text-based .pdf.",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Optional prefix for output files, such as original or revised.",
    )
    parser.add_argument(
        "--agents",
        default=None,
        help="Comma-separated reviewer agent keys to run.",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run selected reviewer agents concurrently.",
    )
    parser.add_argument(
        "--target-role",
        default=None,
        help="Optional target role used by adaptive escalation rules.",
    )
    args = parser.parse_args()

    run_result = run_review(
        input_path=args.input,
        profile=args.profile,
        model_override=args.model,
        output_prefix=args.output_prefix,
        agent_keys=args.agents,
        parallel=args.parallel,
        target_role=args.target_role,
    )
    results = run_result["reviews"]
    aggregate = run_result["summary"]

    print_summary_table(results)
    print(f"\nFinal overall rating: {aggregate['final_overall_rating']}")
    print(f"Average confidence: {aggregate['average_confidence']:.2f}")
    if "adaptive" in aggregate:
        adaptive = aggregate["adaptive"]
        print(f"First pass runtime: {adaptive['first_pass_runtime_seconds']:.2f}s")
        print(f"Escalated agents: {', '.join(adaptive['escalated_agents']) or 'none'}")
        for persona, reasons in adaptive["escalation_reasons"].items():
            print(f"- {persona}: {'; '.join(reasons)}")
        print(f"Escalation runtime: {adaptive['escalation_runtime_seconds']:.2f}s")
    print(f"Total runtime: {aggregate['total_runtime_seconds']:.2f}s")
    print(f"Saved reviews: {run_result['reviews_path']}")
    print(f"Saved summary: {run_result['summary_path']}")


if __name__ == "__main__":
    main()
