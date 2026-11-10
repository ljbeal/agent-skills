---
name: Create Issues
description: Create issues in the repository's tracker, one per defect or feature. Use when the user wants findings, gaps, or defects turned into issues or work items.
---

# Create Issues

Create one issue per defect or feature, in the repository's issue tracker.
Batch creation is expected: the user provides a list, you create all items,
then report the results.

## Conventions

- **One issue per defect.** Never merge two distinct defects into one issue.
- **Title.** Short, imperative, phrased as intended for the final merge.
  Name the outcome, not the symptom. No trailing period.
  - Good: `Persist failed results to database`
  - Bad: `DB crashes when a job fails`
- **Description.** Outline the issue, do not describe the current state.
  - First paragraph: what breaks or what is missing, with the specific
    identifiers (class, method, field, constraint) and the exact error where
    one exists.
  - Bullet list: the target behaviour. Each bullet is one verifiable outcome.
- **Status updates** go in issue comments. Never rewrite the title or
  description to track progress.

## Milestones

Every issue, and the merge request that resolves it, attaches to a version
milestone. The milestone title is the bare version string (for example
`0.15.1`), with no `v` prefix.

- The next version is derived from the repository's version file (for example
  `pyproject.toml` or `setup.py` for Python, `Cargo.toml`, `package.json`):
  patch +1 on the current version, unless the user names a different version.
- At discovery, list the active milestones. Exactly one: attach every new
  issue to it. Several: ask the user which milestone each issue belongs to.
  None: propose creating the next-version milestone derived above, and create
  it only after the user confirms.
- Attaching an issue to a milestone, or moving it, is never silent. If the
  user names a milestone, use it as given.
- The merge request attaches to its issue's milestone when it is created
  (the `work-issue` skill handles this; it is not a step in this skill).

## Reproduction

Reproduce and explore every defect fully before creating its issue.

- Run the failing command yourself and capture the exact error.
- Trace the relevant code path to the root cause. File the issue against
  the cause, not the symptom.
- If the defect does not reproduce in your environment, say so, record what
  was tried, and ask the reporter for environment details before creating
  the issue.

## Workflow

1. Discover the tracker tool and its conventions. Check the repository docs
   (AGENTS.md, CONTRIBUTING.md) and existing issues. Note the CLI (for example
   `glab` for GitLab, `gh` for GitHub) and the highest existing issue number.
   On GitLab, `scripts/glab_query.py issues --next-id` (next to this skills
   directory) prints that number + 1; note `glab issue list` prints nothing
   in work-items projects, while the script's issues subcommand works.
   Also list the active version milestones (`scripts/glab_query.py milestones`
   or `glab milestone list --state active`) and pick the target milestone per
   the Milestones section: the single active one, or after asking, or a newly
   proposed one.
2. For each item, create the issue with the tracker CLI, attached to its
   milestone (on GitLab, `glab issue create --milestone <title>`). Pass
   multi-line descriptions via a heredoc so the shell does not mangle them.
   Collect every returned URL as it appears.
3. Verify with the tracker CLI that every item exists, is open, and is
   attached to the milestone it was created under
   (`scripts/glab_query.py issues --milestone <title>`).
4. Report a table: number, title, milestone, scope. Offer to start work on
   any of them. Branch and merge request creation belong to the `work-issue`
   skill, not here.

## Rules

- Do not create branches or merge requests in this skill.
- Do not edit code in this skill.
- Do not create an issue without a milestone unless the user explicitly
  declines one.
- If the user has not specified priority order, do not invent one. Present the
  list and let the user choose.

## Per-repo override

This is the generic skill. Be sure to check for local overrides, or additional
instructions such as AGENTS.md
