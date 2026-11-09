#!/usr/bin/env python3
"""Query helpers for glab/GitLab.

General purpose: works in any glab-authenticated GitLab repository. The
project is resolved automatically from the current git repository (glab's
project view, falling back to the origin remote URL). Data is fetched with
`glab api` and parsed here, so all of glab's auth handling still applies.

Subcommands:
  issues      List issues (work items): --state, --limit, --next-id, --milestone
  milestones  List milestones with progress: --state active|closed|all, --no-progress
  pipelines   List recent pipelines: --ref, --limit
  jobs        Jobs and statuses of one pipeline (long external ID)

Examples:
  glab_query.py issues --state opened
  glab_query.py issues --next-id
  glab_query.py issues --milestone 0.15.1
  glab_query.py milestones
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


def milestone_title(issue):
    m = issue.get("milestone")
    return m.get("title") if m else ""


def cmd_issues(args):
    endpoint = f"issues?state={args.state}&per_page=100"
    data = api(endpoint)
    if args.next_id:
        # issue IDs are project-wide, so never apply the milestone filter first
        print(max((i["iid"] for i in data), default=0) + 1)
        return
    if args.milestone:
        data = [i for i in data if milestone_title(i) == args.milestone]
    data.sort(key=lambda i: i["iid"], reverse=True)
    for issue in data[: args.limit]:
        print(
            f"{issue['iid']:>5}  {issue['state']:<8}  "
            f"{label_names(issue):<24}  {milestone_title(issue):<12}  "
            f"{issue['title']}"
        )


def all_issues():
    """Every issue in the project (opened and closed), paged."""
    out = []
    for state in ("opened", "closed"):
        page = 1
        while True:
            data = api(f"issues?state={state}&per_page=100&page={page}")
            out.extend(data)
            if len(data) < 100:
                break
            page += 1
    return out


def milestone_counts():
    """Issue counts per milestone title, by state (client-side: the REST
    milestones response carries no issue counts)."""
    counts = {"opened": {}, "closed": {}}
    for issue in all_issues():
        title = milestone_title(issue)
        if title:
            counts[issue["state"]][title] = counts[issue["state"]].get(title, 0) + 1
    return counts


def merge_request_counts(titles):
    """MR counts per milestone title: open and done (merged + closed). One
    paged query per state per milestone; the API's milestone filter works on
    MRs, unlike on issues."""
    counts = {t: {"open": 0, "done": 0} for t in titles}
    for state, key in (("opened", "open"), ("merged", "done"), ("closed", "done")):
        for title in titles:
            page = 1
            while True:
                data = api(
                    "merge_requests?"
                    f"milestone={urllib.parse.quote(title, safe='')}"
                    f"&state={state}&per_page=100&page={page}"
                )
                counts[title][key] += len(data)
                if len(data) < 100:
                    break
                page += 1
    return counts


def cmd_milestones(args):
    # state values for milestones are active/closed, unlike issues (opened)
    data = api(f"milestones?state={args.state}&per_page=100")
    data.sort(key=lambda m: m["iid"], reverse=True)
    issue_counts = mr_counts = None
    if not args.no_progress:
        issue_counts = milestone_counts()
        mr_counts = merge_request_counts([m["title"] for m in data])
    for m in data:
        title = m["title"]
        done = issue_counts["closed"].get(title, 0) if issue_counts else 0
        pending = issue_counts["opened"].get(title, 0) if issue_counts else 0
        issues = f"{done}/{done + pending} issues" if issue_counts else ""
        mr = mr_counts[title] if mr_counts else None
        mrs = f"{mr['done']}/{mr['done'] + mr['open']} MRs" if mr else ""
        progress = "  ".join(p for p in (issues, mrs) if p)
        desc = (m.get("description") or "").replace("\n", " ")
        print(
            f"{m['iid']:>5}  {m['state']:<7}  {title:<16}  {progress:<24}  "
            f"{m.get('due_date') or 'no due date':<10}  {desc}"
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
    p_issues.add_argument(
        "--milestone",
        default=None,
        help="filter by milestone title (client-side: the API's milestone_title "
        "parameter is ignored on work-items projects)",
    )
    p_issues.set_defaults(func=cmd_issues)

    p_miles = sub.add_parser(
        "milestones", help="list milestones with issue progress"
    )
    p_miles.add_argument(
        "--state",
        default="active",
        choices=["active", "closed", "all"],
        help="milestone state (note: active, not opened)",
    )
    p_miles.add_argument(
        "--no-progress",
        action="store_true",
        help="skip counting issues (fewer API calls)",
    )
    p_miles.set_defaults(func=cmd_milestones)

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
