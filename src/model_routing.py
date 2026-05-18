"""Model routing helpers for local Ollama reviewer agents."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUTING_PATH = ROOT / "configs" / "model_routing.yaml"


def load_model_routing(path: str | Path = DEFAULT_ROUTING_PATH) -> dict:
    """Load model routing profiles from YAML."""

    routing_path = Path(path)
    with routing_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Model routing config must be a mapping: {routing_path}")
    return data


def resolve_agent_model(
    profile_name: str,
    agent_key: str,
    manual_model: str | None = None,
    routing: dict | None = None,
) -> str:
    """Resolve the Ollama model for one agent.

    A manual model override takes precedence over all profile routing.
    """

    if manual_model:
        return manual_model

    routing = routing if routing is not None else load_model_routing()
    profile = routing.get(profile_name)
    if not isinstance(profile, dict):
        valid = ", ".join(sorted(routing)) or "none"
        raise ValueError(f"Unknown model profile '{profile_name}'. Valid profiles: {valid}")

    model = profile.get(agent_key) or profile.get("default_model")
    if not model:
        raise ValueError(
            f"Profile '{profile_name}' has no model for agent '{agent_key}' "
            "and no default_model."
        )
    return str(model)


def get_adaptive_config(routing: dict | None = None) -> dict:
    """Return the adaptive routing configuration."""

    routing = routing if routing is not None else load_model_routing()
    config = routing.get("adaptive")
    if not isinstance(config, dict):
        raise ValueError("Missing adaptive profile in model routing config.")
    for key in ["first_pass_model", "escalation_model"]:
        if not config.get(key):
            raise ValueError(f"Adaptive profile is missing required key: {key}")
    return config

