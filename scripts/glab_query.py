#!/usr/bin/env python3
"""Query helpers for glab/GitLab.

General purpose: works in any glab-authenticated GitLab repository. The
project is resolved automatically from the current git repository (glab's
project view, falling back to the origin remote URL). Data is fetched with
`glab api` and parsed here, so all of glab's auth handling still applies.

Subcommands:
  issues     List issues (work items): --state, --limit, --next-id
  pipelines  List recent pipelines: --ref, --limit
  jobs       Jobs and statuses of one pipeline (long external ID)

Examples:
  glab_query.py issues --state opened
  glab_query.py issues --next-id
  glab_query.py pipelines --ref devel --limit 5
  glab_query.py jobs 3003993071

Exit codes:
  jobs prints 0/1: 1 if any job is failed or canceled, 0 otherwise.
  Any other error exits 2 with a message on stderr.
"""

import argparse
import json
import subprocess
import sys
import urllib.parse


def run_glab(*args):
    result = subprocess.run(["glab", *args], capture_output=True, text=True)
    if result.returncode != 0:
        die(f"glab {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def die(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def project_path():
    """namespace/name of the current project, preferring glab's resolution."""
    try:
        raw = run_glab("project", "view", "-F", "json")
        path = json.loads(raw).get("path_with_namespace", "")
        if path:
            return path
    except (json.JSONDecodeError, subprocess.CalledProcessError):
        pass
    url = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True
    ).stdout.strip()
    if url.startswith(("http://", "https://")):
        path = url.split("://", 1)[1].split("/", 1)[1]
    elif ":" in url:
        path = url.split(":", 1)[1]
    else:
        return ""
    return path.removesuffix(".git")


def api(endpoint):
    """GET a project-scoped endpoint; expect a JSON list."""
    path = project_path()
    if not path:
        die("could not resolve the project path (not a git repo? no glab?)")
    raw = run_glab("api", f"projects/{urllib.parse.quote(path, safe='')}/{endpoint}")
    data = json.loads(raw)
    if not isinstance(data, list):
        # GitLab returns error objects (dicts) for bad parameters, e.g.
        # sort=created_desc on issues. Surface that instead of crashing.
        die(f"expected a list from {endpoint}, got: {str(data)[:200]}")
    return data


def label_names(issue):
    # labels arrive as plain strings in some responses and as
    # {name: ...} objects in others; normalise both
    return ",".join(
        label if isinstance(label, str) else label.get("name", "")
        for label in issue.get("labels", [])
    )


def current_branch():
    return subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    ).stdout.strip()


def cmd_issues(args):
    data = api(f"issues?state={args.state}&per_page=100")
    if args.next_id:
        print(max((i["iid"] for i in data), default=0) + 1)
        return
    data.sort(key=lambda i: i["iid"], reverse=True)
    for issue in data[: args.limit]:
        print(
            f"{issue['iid']:>5}  {issue['state']:<8}  "
            f"{label_names(issue):<24}  {issue['title']}"
        )


def cmd_pipelines(args):
    ref = args.ref or current_branch()
    endpoint = f"pipelines?per_page={args.limit}"
    if ref:
        endpoint = (
            f"pipelines?ref={urllib.parse.quote(ref, safe='')}&per_page={args.limit}"
        )
    data = api(endpoint)
    data.sort(key=lambda p: p["id"], reverse=True)
    for p in data:
        print(
            f"{p['id']}  {p['iid']}  {p['status']:<12}  "
            f"{p['ref']:<24}  {p['sha'][:8]}  {p['created_at']}"
        )


def cmd_jobs(args):
    data = api(f"pipelines/{args.pipeline_id}/jobs?per_page=100")
    bad = 0
    for job in data:
        if job["status"] in ("failed", "canceled"):
            bad = 1
        print(f"{job['status']:<12}  {job['name']}")
    sys.exit(bad)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_issues = sub.add_parser("issues", help="list issues (work items)")
    p_issues.add_argument(
        "--state", default="all", choices=["opened", "closed", "all"]
    )
    p_issues.add_argument("--limit", type=int, default=20)
    p_issues.add_argument(
        "--next-id",
        action="store_true",
        help="print the next unused issue number and exit",
    )
    p_issues.set_defaults(func=cmd_issues)

    p_pipes = sub.add_parser("pipelines", help="list recent pipelines")
    p_pipes.add_argument(
        "--ref", default=None, help="branch/tag filter (default: current branch)"
    )
    p_pipes.add_argument("--limit", type=int, default=10)
    p_pipes.set_defaults(func=cmd_pipelines)

    p_jobs = sub.add_parser("jobs", help="jobs and statuses of one pipeline")
    p_jobs.add_argument(
        "pipeline_id",
        help="long external pipeline ID (the short iid in parentheses 404s)",
    )
    p_jobs.set_defaults(func=cmd_jobs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
