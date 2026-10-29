# glab query scripts

General helpers for extracting information from glab/GitLab. Works in any
glab-authenticated GitLab repository: the project is resolved automatically
from the current git repository (glab's project view, falling back to the
origin remote URL), and data is fetched with `glab api`, so all of glab's
auth handling still applies.

| Script | Purpose |
|---|---|
| `glab_query.py issues` | List issues (work items): `--state opened\|closed\|all`, `--limit N`, `--next-id` |
| `glab_query.py pipelines` | List recent pipelines: `--ref <ref>` (default: current branch), `--limit N` |
| `glab_query.py jobs <pipeline-id>` | Jobs and statuses of one pipeline; takes the long external ID |

Examples:

```sh
scripts/glab_query.py issues --state opened
scripts/glab_query.py issues --next-id
scripts/glab_query.py pipelines --ref devel --limit 5
scripts/glab_query.py jobs 3003993071
```

`jobs` exits 1 if any job is failed or canceled (0 otherwise), so it can
gate a shell script. Any other error exits 2 with a message on stderr.

## API quirks these scripts work around

- `glab issue list` prints nothing in projects that use work items, but the
  `issues` REST endpoint still returns them. The script uses the endpoint.
- The `labels` field arrives as plain strings in some responses and as
  `{name: ...}` objects in others. `glab_query.py` normalises both.
- `sort=created_desc` on the issues endpoint returns an error object instead
  of a list. Fetch and sort client-side by `iid` instead.
- The pipelines endpoint filters by `status`, not `state` (issues take
  `state`). The script filters by `ref` only and never passes `sort=`.
- `glab ci get --pipeline-id` and the API both want the long external
  pipeline ID; the short iid (shown in parentheses by `glab ci list`) 404s.
- `glab project view -F json` reports the current project's metadata
  (`path_with_namespace`, `id`, ...). There is no `--json` or `-f json`
  flag in this glab version.
- GitLab returns error objects (dicts), not a list, for some bad parameters.
  The `api()` helper detects that and reports it instead of crashing with a
  confusing traceback.
