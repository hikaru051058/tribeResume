"""Smoke tests for bounded section evidence extraction."""

from __future__ import annotations

from section_evidence import extract_section_evidence, split_document_sections


SAMPLE = """EDUCATION
State University, B.S. in Computer Science
Relevant Coursework: Artificial Intelligence, Machine Learning, Compiler Design, Computer Security, Edge Computing

EXPERIENCE
SEM Medical Solutions
- Indexed 130,000+ medical reports.
- Reduced workload by 30% and saved 2 hours.
"""


def assert_contains(items: list[str], expected: str) -> None:
    joined = " | ".join(items)
    assert expected.lower() in joined.lower(), f"Expected {expected!r} in {items!r}"


def assert_not_contains(items: list[str], unexpected: str) -> None:
    joined = " | ".join(items)
    assert unexpected.lower() not in joined.lower(), f"Unexpected {unexpected!r} in {items!r}"


def main() -> None:
    sections = split_document_sections(SAMPLE)
    print("sections:", [(item["name"], item["start_line"], item["end_line"]) for item in sections])

    education = extract_section_evidence(SAMPLE, "education")
    coursework = extract_section_evidence(SAMPLE, "coursework")
    experience = extract_section_evidence(SAMPLE, "experience")

    assert_contains(education, "Artificial Intelligence")
    assert_contains(education, "Machine Learning")
    assert_contains(education, "Compiler Design")

    assert_contains(coursework, "Artificial Intelligence")
    assert_contains(coursework, "Machine Learning")
    assert_contains(coursework, "Compiler Design")
    assert_not_contains(coursework, "130,000+")
    assert_not_contains(coursework, "30%")

    assert_contains(experience, "130,000+")
    assert_contains(experience, "30%")

    print("education evidence:", education)
    print("coursework evidence:", coursework)
    print("experience evidence:", experience)
    print("section evidence tests passed")


if __name__ == "__main__":
    main()

