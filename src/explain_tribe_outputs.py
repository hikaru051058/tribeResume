"""Plain-English explanations for TRIBE-style perception features."""

from __future__ import annotations


def explain_response_intensity() -> str:
    """Explain response intensity in cautious product language."""

    return (
        "Response intensity is a proxy summary of predicted response magnitude over the "
        "document stimulus. Higher intensity may suggest that a section produces a stronger "
        "predicted response pattern, but it does not prove attention, comprehension, or quality."
    )


def explain_section_salience() -> str:
    """Explain section salience in cautious product language."""

    return (
        "Section salience estimates which document sections may stand out relative to other "
        "sections. It is a prioritization signal for inspection, not evidence that a real reader "
        "will focus there."
    )


def explain_cognitive_load_proxy() -> str:
    """Explain cognitive-load proxy in cautious product language."""

    return (
        "The cognitive-load proxy combines density-like and response-variability signals. It may "
        "suggest that a section could feel effortful, crowded, or hard to scan, but it is not a "
        "direct measurement of reader confusion."
    )


def explain_underemphasis_proxy() -> str:
    """Explain underemphasis proxy in cautious product language."""

    return (
        "The underemphasis proxy flags sections that may be less salient than expected. It can "
        "help identify strong evidence that might be visually or cognitively buried."
    )


def explain_mock_vs_real_source(perception_source: str) -> str:
    """Explain the difference between mock and real TRIBE-style sources."""

    if perception_source == "mock":
        return (
            "This report uses mock TRIBE-style data for development. It is not real TRIBE output, "
            "not neuroscience evidence, and not a measured reader response."
        )
    return (
        "This report uses a real TRIBE-style prediction source, but the result is still an "
        "experimental proxy signal. It should not be treated as actual brain activity or a hiring "
        "outcome prediction."
    )


def build_tribe_output_explanation(perception_source: str) -> dict:
    """Build the standard explanation block for perception reports."""

    return {
        "what_raw_output_means": explain_response_intensity(),
        "what_features_mean": " ".join(
            [
                explain_section_salience(),
                explain_cognitive_load_proxy(),
                explain_underemphasis_proxy(),
            ]
        ),
        "what_cannot_be_concluded": (
            f"{explain_mock_vs_real_source(perception_source)} The system cannot conclude actual "
            "reader perception, recruiter decisions, admissions outcomes, or resume quality from "
            "these signals alone."
        ),
    }

