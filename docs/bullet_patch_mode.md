# Bullet Patch Mode

## Why Full Rewrites Are Risky

Full resume rewrites can make a strong technical resume weaker by removing concrete proof: metrics, technologies, company names, project names, dates, and system details. A resume can become cleaner but less credible.

## Why Patch Mode Is Safer

Patch mode treats the original resume as the source of truth. It does not output a full rewritten resume by default. Instead, it suggests targeted bullet edits that the user can manually accept, review, or reject.

Each patch includes:

- Original bullet.
- Proposed bullet.
- Reason for the change.
- Evidence preserved.
- Evidence added from existing context.
- Evidence removed.
- Risk level.
- Accept/review/reject recommendation.

## Evidence Preservation

Patch mode should not delete metrics or technologies. If a patch removes evidence, it must list that evidence and mark the patch as high risk.

This is especially important for AI systems and backend resumes, where credibility often depends on concrete evidence such as:

- Dataset or index sizes.
- User counts.
- Latency or workload reductions.
- Technical stacks.
- CI/CD workflows.
- System names.
- Company and project names.

## Section-Aware Evidence Policy

Evidence from existing context is not always safe. A technology, metric, or domain detail can appear somewhere in the resume but still be invalid for a specific bullet.

Examples of unsafe evidence borrowing:

- Moving medical reporting language from a SEM Medical Solutions bullet into an Arin cosmetic/social recommendation bullet.
- Adding TensorFlow to a SEM platform bullet when TensorFlow only appears under Opaque Hand or the general skills section.
- Reframing a Niftiq blockchain ticketing project as AI medical reporting.

Patch validation now checks the bullet's local company or project section. Added evidence must appear in the same section as the original bullet. If it appears only somewhere else in the resume, the patch is flagged as cross-section evidence contamination.

## Entity Drift

Entity drift happens when a patch changes the company, project, product domain, or factual context of a bullet.

Examples:

- Arin/cosmetic recommendation platform -> medical reporting platform.
- Opaque Hand/prosthetic prototype -> SEM medical reporting.
- Niftiq/blockchain ticketing -> AI medical reporting.

Patches with entity drift should never be accepted automatically. They should be marked for review or rejection, even if the model originally called them low risk.

## Manual Review Workflow

Run patch generation:

```bash
python src/run_bullet_patch.py \
  --input path/to/resume.pdf \
  --model qwen3:14b \
  --target-role "AI backend engineer intern" \
  --focus "AI/ML specificity"
```

Then inspect:

```text
outputs/bullet_patches.json
outputs/bullet_patches.md
```

Accept low-risk patches directly only if the proposed wording is accurate. Review medium-risk patches carefully. Reject high-risk patches that remove evidence or add unsupported specificity.

## Why This Is Better For Strong Technical Resumes

Strong technical resumes often need sharper framing, not broad simplification. Patch mode helps improve the weakest bullets while preserving the details that make the resume credible.
