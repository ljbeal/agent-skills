---
name: Close Issue
description: Final review and close of a completed issue. Reviews the incoming code as a whole, then merges and closes. Use when the user wants to close, complete, or finalize an issue.
---

# Close Issue

Close an issue only after a final review of the complete incoming change. The
review considers the incoming code as a whole: the aggregated diff from base
to head, not commit by commit. Code that passes commit by commit can still be
wrong as a unit. The whole-diff review is the gate for close.

The purpose of this skill is code review and discussion, not merge mechanics.
The merge happens only after every review finding has been resolved or
explicitly waived. An issue closed with unresolved findings forces a
follow-up issue; a merge that takes a few extra discussion steps does not.
Prefer the discussion.

## Discover repo values

Before starting, establish from the repository docs (AGENTS.md, CI config) and
existing branches and merge requests:

- The development branch (merge target)
- The test layout, and how to run one test file and a full area (including
  parallel flags and any required environment variables or interpreter path)
- The linter and formatter commands
- The merge style (merge, squash, or rebase)
- The tracker CLI and its close-link format (for example `Closes #N`)

## Pipeline status

If the repository has CI, the pipeline for the merge request's head commit
must be green before close. Check it with the tracker CLI.

With `glab` (GitLab):

- On the source branch, `glab ci get` reports the latest pipeline for the
  current branch. Off the branch, find the row in `glab ci list` and use
  `glab ci get --pipeline-id <id>`.
- `glab ci list` shows two numbers per pipeline: the long external ID and a
  short IID in parentheses. `glab ci get --pipeline-id` wants the external
  ID; the short IID 404s.
- Read the `status:` line and the per-job lines. Job log:
  `glab ci trace <job-name> --pipeline-id <id>`.
- Retry a failed job: `glab ci retry <job-name> --pipeline-id <id>`.
- Helpers next to this skills directory: `scripts/glab_query.py pipelines`
  finds a pipeline by ref; `scripts/glab_query.py jobs <id>` lists job
  statuses and exits 1 on a failed or canceled job.
- Avoid `glab ci status`: it reports a single job, not the pipeline.
- Poll in a loop over `glab ci get` until `status:` reads `success`,
  `failed`, or `canceled`. Test jobs can take many minutes.

A green pipeline reached by retrying a flaky job is acceptable. Name the
retry in the closing comment.

With `gh` (GitHub): `gh run list --branch <branch>` for the run,
`gh run view <id> --json status,conclusion` for state,
`gh run view <id> --log-failed` for the failing log, and
`gh run re-run <id> --failed` to retry.

## Workflow

1. Confirm the issue, its branch, and its merge request with the tracker CLI.
   The merge request must be un-drafted and green.
2. Re-run the verification from the `work-issue` skill: the affected tests,
   the full affected suite, and the linter and formatter on changed files.
3. Build the review surface:
   - The aggregated diff, base to head: `git diff <dev>...<head>`.
   - The final state of every file the diff touches. Read whole files, not
     diff hunks.
   - The commit list of the branch, in order.
4. Review the incoming code as a whole:
   - **Requirement coverage.** Check the final result against every bullet of
     the issue description. Each bullet must be met by the merged outcome, not
     by any single commit.
   - **Cross-commit consistency.** Later commits that supersede or reverse
     earlier ones, half-done intermediate state, dead code, unused imports,
     debug leftovers, comments that describe an abandoned approach.
   - **Integration.** Callers of changed APIs updated, naming and style
     consistent with the surrounding unchanged code, docstrings and docs
     matching the new behaviour.
   - **Scope.** No behaviour changes outside the issue's scope that are not
     explained by a commit message.
5. Report findings by severity: blocking, non-blocking, notes.
   A finding is anything a careful reviewer would flag to a teammate:
   requirement gaps, dead code, missing or stale docs, behavioural
   consequences outside the stated scope, and pre-existing problems in files
   the diff touches. Do not downgrade a finding to keep the merge moving.
6. Resolve or waive every finding. This is a discussion step, and the gate
   for merge:
   - For each finding, present the options: fix it on the branch, or waive
     it with a reason. Include the concrete proposed fix when one exists.
   - A fix is a code change: propose the approach, await approval, apply it,
     re-run the verification from step 2, and re-review the affected area on
     the new head.
   - A waiver requires the human's explicit acceptance. Record waivers in a
     merge request comment.
   - Never waive a finding yourself. Never merge while any finding is open.
7. Merge and close, only when no finding is left open:
   - Confirm the source branch still merges cleanly into the development
     branch. If not, rebase it onto the development branch:
     - Clean rebase: confirm the aggregated diff is unchanged, re-run
       verification, force-push with lease, wait for a green pipeline.
     - Conflicted rebase: resolve the conflicts as a code change
       (propose, await approval), then redo the whole-diff review.
   - Drop the draft marker from the merge request title if one is still
     present.
   - Merge the merge request with the repository merge style.
   - Post a short closing comment on the issue: review outcome plus the
     merge commit or merge request reference. Name any retried jobs.
   - Close the issue with the tracker CLI. If the close link did not auto-
     close it, close it explicitly.

## Rules

- Never close an issue while its merge request is red, draft, or unmerged.
- Never close on the basis of a per-commit review. The whole-diff review is
  mandatory.
- Never merge while any review finding is still open. Every finding must be
  fixed and re-verified, or explicitly waived by the human. The merge is the
  last step, not the default outcome.
- Do not edit code in this skill unless a finding is being fixed. A fix is a
  large edit: propose the approach and await approval first.
- Keep the closing comment short. Status lives in comments, never in the
  title or description.

## Per-repo override

This is the generic skill. If this generic version loaded, no project-local
override exists for this repository. After discovering the repo values above,
propose a project-local override at `.opencode/skills/close-issue/SKILL.md`
that inlines those concrete values (merge style, exact test and lint commands,
tracker CLI and close command, review checklist tuned to the repository).

Create overrides on a per-repo basis: each repository, or each package within
a monorepo that owns its own workflow, gets its own `.opencode/skills`
directory (nested package directories are discovered as well). Commit
overrides to the repository's default branch as tooling, not to a feature
branch.
