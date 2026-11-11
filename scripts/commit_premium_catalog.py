"""Create the reviewed 20 nonempty commits; never force-push or stage other files."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Create commits after validating the plan")
    parser.add_argument("--push", action="store_true", help="Push main after verifying remote ancestry")
    options = parser.parse_args()
    if options.push and not options.execute:
        parser.error("--push requires --execute")
    plan = json.loads((ROOT / "docs/premium_commit_plan.json").read_text(encoding="utf-8"))
    if len(plan["commits"]) != 20:
        raise ValueError("The release plan must contain exactly 20 functional commits.")
    if git("branch", "--show-current").stdout.strip() != plan["branch"]:
        raise ValueError("Run from main; no automatic branch switching is performed.")
    listed = []
    for group in plan["commits"]:
        if not group["message"].strip() or not group["paths"]:
            raise ValueError("Empty commit group.")
        for name in group["paths"]:
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or ".git" in path.parts or not path.is_file():
                raise ValueError(f"Invalid or missing planned file: {name}")
            listed.append(name)
    if len(listed) != len(set(listed)):
        raise ValueError("A file appears in more than one commit group.")
    changed = set(git("diff", "--name-only", "HEAD").stdout.splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").stdout.splitlines())
    unknown = changed - set(listed)
    if unknown:
        raise ValueError(f"Unplanned changes must be reviewed first: {sorted(unknown)}")
    staged = git("diff", "--cached", "--name-only").stdout.strip()
    if staged:
        raise ValueError("Existing staged changes found; review the index before continuing.")
    base = plan["base_commit"]
    if git("merge-base", "--is-ancestor", base, "HEAD", check=False).returncode:
        raise ValueError("The reviewed base commit is not an ancestor of HEAD.")
    completed = git("log", "--reverse", "--format=%s", base + "..HEAD").stdout.splitlines()
    expected = [group["message"] for group in plan["commits"]]
    if completed != expected[:len(completed)] or len(completed) > 20:
        raise ValueError("History differs from the reviewed plan; do not rewrite it automatically.")
    for index, group in enumerate(plan["commits"], 1):
        state = "completed" if index <= len(completed) else "planned"
        print(f"{index:02d}. [{state}] {group['message']}")
    if not options.execute:
        print("Dry run: no index writes, commits or network actions.")
        return
    git("var", "GIT_AUTHOR_IDENT")  # Ensure configured author, without inventing identity.
    for group in plan["commits"][len(completed):]:
        git("add", "--", *group["paths"])
        result = git("diff", "--cached", "--quiet", check=False)
        if result.returncode == 0:
            raise ValueError(f"Refusing an empty commit: {group['message']}")
        if result.returncode != 1:
            raise ValueError(result.stderr)
        git("diff", "--cached", "--check")
        git("commit", "-m", group["message"])
    if options.push:
        git("fetch", plan["remote"], plan["branch"])
        if git("merge-base", "--is-ancestor", f"{plan['remote']}/{plan['branch']}", "HEAD", check=False).returncode:
            raise ValueError("Remote main diverged. Review and integrate remote changes before pushing.")
        git("push", plan["remote"], "HEAD:" + plan["branch"])
    print("Completed reviewed commits.")


if __name__ == "__main__":
    try:
        run()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(detail, file=sys.stderr)
        raise SystemExit(1)
