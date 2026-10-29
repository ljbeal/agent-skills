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
2. For each item, create the issue with the tracker CLI. Pass multi-line
   descriptions via a heredoc so the shell does not mangle them. Collect every
   returned URL as it appears.
3. Verify with the tracker CLI that every item exists and is open.
4. Report a table: number, title, scope. Offer to start work on any of them.
   Branch and merge request creation belong to the `work-issue` skill, not
   here.

## Rules

- Do not create branches or merge requests in this skill.
- Do not edit code in this skill.
- If the user has not specified priority order, do not invent one. Present the
  list and let the user choose.

## Per-repo override

This is the generic skill. If this generic version loaded, no project-local
override exists for this repository. Apply the conventions above with the
values discovered from the repository docs, and propose a project-local
override at `.opencode/skills/create-issues/SKILL.md` that inlines those
concrete values (tracker CLI and its exact create command, title and
description conventions, verification command, report format).

Create overrides on a per-repo basis: each repository, or each package within
a monorepo that owns its own workflow, gets its own `.opencode/skills`
directory (nested package directories are discovered as well). Commit
overrides to the repository's default branch as tooling, not to a feature
branch.
