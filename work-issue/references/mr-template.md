# Merge Request Description Template (generic)

Fill the placeholders. Keep the structure: defect paragraph, MR scope
paragraph, test list, close link.

```markdown
<One paragraph stating the defect: what breaks, where, and the exact error
where one exists. Name the classes, methods, and fields involved.>

This MR adds the failing tests that outline the issue (#<N>) and the fix that
<target behaviour in one clause>.

## Tests

- `<path>::<test_id>` — <what it asserts, in one clause>
- `<path>::<test_id>` — <what it asserts, in one clause>

Closes #<N>
```

## Rules

- Status updates go in MR comments. Never rewrite this description to track
  progress.
- While the MR carries only failing tests, the title keeps the draft marker
  (for example `Draft: `). Remove it only when the pipeline is green.
