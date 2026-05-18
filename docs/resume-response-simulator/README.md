# Resume Response Simulator

## One-Sentence Pitch

A reader-response simulator for resumes that predicts how different evaluators will perceive a document before the candidate sends it.

## Product Overview

The Resume Response Simulator is not a normal resume checker. It is a structured simulation system that models how different readers respond to the same resume: a technical recruiter, software engineering manager, AI/ML reviewer, graduate admissions reviewer, skeptical reviewer, ATS parser, startup founder, or non-technical HR reader.

The goal is to answer a practical question:

> If this resume lands in front of the wrong or right reader, what reaction will it create in the first pass?

The product parses a resume, extracts a structured candidate profile, simulates evaluator personas, scores the strength of the response, cites exact resume evidence, and suggests targeted rewrites.

## Problem It Solves

Most candidates do not need another generic list of resume tips. They need to know:

- Whether the resume creates a great, good, mixed, weak, or bad response.
- Which reader types will understand the value quickly.
- Which claims feel credible, inflated, confusing, or unsupported.
- Which resume lines create the strongest signal.
- Which lines hurt trust or waste attention.
- Whether a version is better for a specific role or program.

## Why This Is Different From Copy-Pasting Into ChatGPT Or Claude

Copy-pasting a resume into a general LLM is useful for one-off advice. It is also unstructured, inconsistent, and hard to compare across versions.

This system adds value only if it provides:

- Structured evaluator personas instead of one generic assistant voice.
- Evidence-backed judgments tied to exact resume lines.
- Repeatable rubrics and version tracking.
- Confidence scoring based on evidence, not vibes.
- Role-fit comparison against target job descriptions or admissions criteria.
- Disagreement analysis between evaluator types.
- Optional stimulus-response analysis for layout, density, attention, and cognitive load.

For one personal resume review, ChatGPT or Claude may be enough. For a product, the differentiator must be repeatability, evidence, comparison, and calibrated reader simulation.

## Who It Is For

- Job candidates applying to technical, AI/ML, startup, or general roles.
- Students applying to graduate programs, research labs, or internships.
- Career coaches who want structured review artifacts.
- Resume editing services that need repeatable diagnostics.
- Recruiting tools that want candidate-facing feedback.
- Teams comparing resume versions for role targeting.

## MVP Scope

The MVP should focus on the core semantic product:

- Resume upload and text extraction.
- Structured candidate profile extraction.
- Persona-based review agents.
- Overall response label: Great, Good, Mixed, Weak, or Bad.
- First-pass reaction summary.
- Strongest and weakest signals.
- Credibility risks.
- Role-fit scoring.
- Evidence-backed confidence score.
- Bullet rewrite suggestions.
- Basic version comparison.

TRIBE v2-style analysis should not be in the MVP unless there is a clear experiment budget. It can be documented as an optional research layer.

## Long-Term Vision

The long-term product is a simulation lab for professional documents. A user can upload several versions, select target roles, simulate different readers, inspect evidence-backed reactions, and iterate toward a version that produces the desired response.

Long-term extensions:

- Job-specific resume optimization.
- Admissions statement and cover letter simulation.
- Multi-document package review.
- Longitudinal tracking across application outcomes.
- Calibrated scoring against real reviewer feedback.
- Optional layout and attention modeling using stimulus-response techniques.

