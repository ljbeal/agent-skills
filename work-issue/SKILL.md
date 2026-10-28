---
name: Work Issue
description: Work a tracked issue end to end: branch, failing test first, draft merge request, verification, merge. Use when the user wants to start or finish an issue.
---

# Work Issue

Standard pattern: issue first, then branch + merge request. The branch exists
only to feed the merge request; never create one without it.

Phases: **Start** (branch + failing tests + draft merge request), **Finish**
(verify the fix, un-draft, merge). Skip a phase only when the user has already
done it.

## Discover repo values

Before Phase 1, establish from the repository docs (AGENTS.md, CI config) and
from existing branches and merge requests:

- The development branch (merge target)
- The branch naming convention (often `<issue#>-<kebab-slug>`)
- The test layout, and how to run one test file and a full area (including
  parallel flags and any required environment variables or interpreter path)
- The linter and formatter commands
- The tracker CLI and its close-link format (for example `Closes #N`)

## Phase 1: Start

1. Confirm the issue with the tracker CLI if it is not already in context.
2. Create the branch from the development branch on a clean tree, using the
   repository naming convention. Keep the slug short: GitLab builds the merge
   commit subject as `Merge branch '<branch>' into '<target>'` and truncates
   long subjects in the commits list (width-based; ~72 chars is the safe cap).
   Cap the branch name at 40 chars, issue number included, so the full
   subject stays within ~72 chars. If the issue title would exceed that,
   shorten the slug to its most meaningful words and keep the issue number.
3. Write the failing test first.
   - Place it beside the tests for the affected area.
   - Match the style of the neighbouring test files: docstring stating what is
     exercised, shared fixtures, one class per behaviour.
   - Assert the target behaviour: no error on the failing path, and a
     round trip that preserves the data.
4. Run the new test. Confirm it fails with the exact bug, not a collection or
   fixture error.
5. Run the surrounding test area to confirm no collateral breakage. Use the
   repository's parallel flags for large sections. Expected: only the new
   tests fail, everything else passes.
6. Commit the tests following the repository commit convention, referencing
   the issue.
7. Push the branch.
8. Create the merge request. Title prefixed with the draft marker while the
   pipeline is red. Target: the development branch. Description: follow
   `references/mr-template.md`. End the description with the close link to the
   issue.

   The merge request is intentionally red while it carries only failing
   tests. Keep the draft marker until the fix is in and green.

## Phase 2: Finish

The user has implemented the fix (in this branch or elsewhere). Verify, then
close out.

1. Run the new tests. All must pass.
2. Run the full affected suite, with the repository's parallel flags.
3. Run the linter and formatter check on the changed files.
4. Commit and push any remaining changes.
5. Remove the draft marker from the merge request title.
6. Report: tests, suite result, lint result, merge request URL.

## Rules

- Fix code is a large edit. Unless the user has already written it, propose
  the approach and await approval before writing it. Tests may be written
  freely, but must be executed after any change.
- If the new test fails for the wrong reason (fixture, collection, import),
  fix the test. Do not weaken the assertion.
- Never merge the merge request without a green pipeline.

## Per-repo override

This is the generic skill. If this generic version loaded, no project-local
override exists for this repository. After discovering the repo values above,
propose a project-local override at `.opencode/skills/work-issue/SKILL.md`
that inlines those concrete values (branch target and naming, exact test and
lint commands, tracker CLI, MR template), plus its own
`references/mr-template.md`.

Create overrides on a per-repo basis: each repository, or each package within
a monorepo that owns its own workflow, gets its own `.opencode/skills`
directory (nested package directories are discovered as well). Commit
overrides to the repository's default branch as tooling, not to a feature
branch.
