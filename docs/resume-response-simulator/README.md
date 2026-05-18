# Resume Response Simulator

## Current Status

This folder contains early product-planning notes. The current implemented direction has shifted: TRIBE v2 is the core experimental perception layer, Ollama reviewer agents are optional interpretation/comparison tools, and rewrite/patch tools are optional downstream experiments.

For the current workflow, start with:

- `docs/README.md`
- `docs/tribe_core_architecture.md`
- `docs/perception_report_workflow.md`
- `docs/real_tribe_output_interpretation.md`

## One-Sentence Pitch

A document perception simulator for resumes that estimates how a document may land cognitively and semantically before the candidate sends it.

## Product Overview

The current product is not a normal resume checker and not primarily a multi-agent reviewer. It treats a resume as a timed text stimulus, runs TRIBE-style response prediction, extracts section-level proxy signals, and produces a cautious perception report.

Reviewer personas such as technical recruiter, engineering manager, AI/ML reviewer, graduate admissions reviewer, skeptical reviewer, and ATS parser remain useful as optional comparison tools. They are not the core perception signal.

The goal is to answer a practical question:

> Which sections appear salient, dense, underemphasized, or worth inspecting before this document is sent?

The product parses a resume, builds synthetic reading events, runs real or mock TRIBE-style prediction, maps response proxies back to sections, cites resume evidence, and suggests inspection priorities. It does not claim actual perception, measured brain activity, resume quality, or hiring outcomes.

## Problem It Solves

Most candidates do not need another generic list of resume tips. They need to know:

- Which sections may dominate or disappear in the first-pass signal.
- Which sections may be dense or hard to scan.
- Which claims feel credible, inflated, confusing, or unsupported.
- Which resume lines create the strongest signal.
- Which lines hurt trust or waste attention.
- Whether controlled wording variants change proxy signals while preserving facts.

## Why This Is Different From Copy-Pasting Into ChatGPT Or Claude

Copy-pasting a resume into a general LLM is useful for one-off advice. It is also unstructured, inconsistent, and hard to compare across versions.

This system adds value only if it provides:

- Real TRIBE-derived stimulus-response-like signals when available.
- Section-level proxy rankings and timeline analysis.
- Evidence-backed judgments tied to exact resume lines.
- Separate confidence values for text review, perception signal, and fusion.
- Optional reviewer-agent disagreement analysis.
- Controlled variant experiments.

For one personal resume review, ChatGPT or Claude may be enough. For a product, the differentiator must be repeatability, evidence, comparison, and calibrated reader simulation.

## Who It Is For

- Job candidates applying to technical, AI/ML, startup, or general roles.
- Students applying to graduate programs, research labs, or internships.
- Career coaches who want structured review artifacts.
- Resume editing services that need repeatable diagnostics.
- Recruiting tools that want candidate-facing feedback.
- Teams comparing resume versions for role targeting.

## MVP Scope

The current implementation focuses on the perception-report product:

- Resume upload and text extraction.
- Canonical TRIBE/neuralset text events.
- Real TRIBE probe and dry-run diagnostics.
- Per-segment prediction statistics.
- Timeline-to-section mapping.
- Salience, position-normalized salience, cognitive-load, and underemphasis proxies.
- Human-readable perception reports.
- Optional reviewer comparison, fusion, patch suggestions, and variant comparison.

Mock mode is development-only. Real TRIBE mode is required for serious experimental reports, and even real mode remains a proxy because the inputs are synthetic reading events.

## Long-Term Vision

The long-term product is a simulation lab for professional documents. A user can upload several versions, select target roles, simulate different readers, inspect evidence-backed reactions, and iterate toward a version that produces the desired response.

Long-term extensions:

- Job-specific resume optimization.
- Admissions statement and cover letter simulation.
- Multi-document package review.
- Longitudinal tracking across application outcomes.
- Calibrated scoring against real reviewer feedback.
- Optional layout and attention modeling using stimulus-response techniques.
