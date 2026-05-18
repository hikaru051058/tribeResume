"""Rule-based extraction of concrete resume evidence."""

from __future__ import annotations

import re


TECHNOLOGIES = [
    "Python",
    "JavaScript",
    "TypeScript",
    "SQL",
    "PostgreSQL",
    "FastAPI",
    "Flask",
    "React",
    "Node.js",
    "Docker",
    "Dockerized",
    "Kubernetes",
    "CI/CD",
    "AWS",
    "GCP",
    "Azure",
    "Elasticsearch",
    "Redis",
    "MongoDB",
    "PyTorch",
    "TensorFlow",
    "Scikit-learn",
    "LangChain",
    "OpenAI",
    "LLM",
    "RAG",
    "NLP",
    "Computer Vision",
    "Machine Learning",
    "AI",
    "Git",
    "Linux",
]


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        normalized = re.sub(r"\s+", " ", item.strip())
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def extract_numeric_evidence(text: str) -> list[str]:
    """Extract metrics, dates, ranges, money, counts, and time values."""

    patterns = [
        r"\$[0-9][0-9,]*(?:\.\d+)?\s*(?:k|K|m|M|million|billion)?",
        r"\b\d+(?:\.\d+)?\s*%",
        r"\b\d[\d,]*\+",
        r"\b\d+(?:\.\d+)?\s*(?:ms|milliseconds|s|sec|seconds|minutes|hours|hrs|days)\b",
        r"\b(?:reduced|improved|increased|decreased|cut|raised|indexed|processed|served|supported)\s+[^.\n;]*?\d[^.\n;]*",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|June|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*(?:[-–]\s*(?:Present|Current|(?:Jan|Feb|Mar|Apr|May|Jun|June|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}))?",
        r"\b\d{1,2}/\d{4}\s*[-–]\s*(?:Present|Current|\d{1,2}/\d{4})",
        r"\b(?:19|20)\d{2}\b",
    ]
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return _unique([match if isinstance(match, str) else match[0] for match in matches])


def extract_technology_evidence(text: str) -> list[str]:
    """Extract known technology names from resume text."""

    found = []
    for technology in TECHNOLOGIES:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(technology) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(technology)
    return _unique(found)


def extract_named_evidence(text: str) -> list[str]:
    """Extract likely company, project, school, role, and publication names."""

    evidence = []
    section_headers = {
        "education",
        "experience",
        "projects",
        "skills",
        "coursework",
        "publications",
    }
    for raw_line in text.splitlines():
        line = raw_line.strip(" •-\t")
        if not line:
            continue
        lowered = line.lower().strip(":")
        if lowered in section_headers:
            continue
        if any(marker in line.lower() for marker in [" engineer", " intern", " assistant", "developer", "researcher"]):
            evidence.append(line)
        elif re.search(r"\b(?:University|College|Institute|Solutions|Systems|Labs|Inc|LLC|AI|Platform|Tool)\b", line):
            evidence.append(line)
        elif len(line.split()) <= 6 and re.search(r"[A-Z][a-z]+", line):
            evidence.append(line)
    return _unique(evidence)


def extract_resume_evidence(text: str) -> dict:
    """Extract concrete evidence groups from resume text."""

    numeric = extract_numeric_evidence(text)
    technologies = extract_technology_evidence(text)
    named = extract_named_evidence(text)
    return {
        "numeric": numeric,
        "technologies": technologies,
        "named": named,
        "all": _unique(numeric + technologies + named),
    }
