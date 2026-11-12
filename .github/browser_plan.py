"""Which browser checks a change needs, so CI does not spend 18 minutes in Chrome on a README edit.

Run from the repository root:
    python .github/browser_plan.py BASE        files changed between BASE and HEAD decide
    python .github/browser_plan.py             no BASE (weekly run, manual run, new branch, force push): everything
Prints the matrix for the browser job as JSON. Each entry is one runner: `basics` is "all" (with `shard` K/N), some
lesson ids, or "" for none; `project` is "all", some project names, or "".

- Only README.md, home/, .github/assets/, notes or other text files: no browser check (check.py and deploy still run).
- Only some lessons (basics/lessons/<id>/, basics/dist/<id>/): just those lessons. Likewise one project's folder.
- The shared template, the page-building tools, fonts, course.json or site.json, or this workflow: everything, with
  the basics lessons split over SHARDS runners.
"""
import json
import subprocess
import sys
from pathlib import Path

SHARDS = 4
ROOT = Path(__file__).resolve().parent.parent
ALL = "all"

# Changing one of these changes every page of that module, or how the check works.
EVERYTHING = (".github/workflows/check.yml", ".github/browser_plan.py")
BASICS_ALL = ("basics/template/", "basics/vendor/", "basics/course.json", "basics/site.json", "basics/dist/index.html",
              "basics/tools/build.py", "basics/tools/algo.py", "basics/tools/check_browser.mjs")
# Project decks are built from basics' page, theme, script, fonts and IDE settings.
PROJECT_ALL = ("project/template/", "project/site.json", "project/dist/index.html", "project/tools/build.py",
               "project/tools/stagefiles.py", "project/tools/check_browser.mjs",
               "basics/template/", "basics/vendor/", "basics/site.json")


def changed(base):
    """The files changed since base, or None when base is missing or unknown here."""
    if not base or set(base) == {"0"}:
        return None
    if subprocess.run(["git", "cat-file", "-e", base + "^{commit}"], cwd=ROOT, capture_output=True).returncode:
        return None
    out = subprocess.run(["git", "diff", "--name-only", base, "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.split()


def pick(files):
    """(lessons, projects): each is ALL or a sorted list of names, empty when nothing needs a browser."""
    lessons_known = [item["id"] for item in json.loads((ROOT / "basics/course.json").read_text(encoding="utf-8")) if "id" in item]
    projects_known = json.loads((ROOT / "project/site.json").read_text(encoding="utf-8"))["projects"]
    lessons, projects = set(), set()
    for f in files:
        if f in EVERYTHING:
            return ALL, ALL
        if f.startswith(BASICS_ALL):
            lessons.add(ALL)
        if f.startswith(PROJECT_ALL):
            projects.add(ALL)
        parts = f.split("/")
        if parts[0] == "basics" and len(parts) > 3 and parts[1] in ("lessons", "dist"):
            # a lesson folder that course.json no longer lists means the course changed: check everything
            lessons.add(parts[2] if parts[2] in lessons_known else ALL)
        if parts[0] == "project" and len(parts) > 2:
            name = parts[2] if parts[1] == "dist" and len(parts) > 3 else parts[1]
            if name in projects_known:
                projects.add(name)
    return (ALL if ALL in lessons else sorted(lessons)), (ALL if ALL in projects else sorted(projects))


def matrix(lessons, projects):
    project = projects if projects == ALL else " ".join(projects)
    if lessons == ALL:
        runs = [{"basics": ALL, "shard": "%d/%d" % (k, SHARDS), "project": project if k == 1 else ""} for k in range(1, SHARDS + 1)]
    else:
        runs = [{"basics": " ".join(lessons), "shard": "", "project": project}]
    for run in runs:
        shown = ["basics " + (run["shard"] if run["basics"] == ALL else run["basics"])] if run["basics"] else []
        shown += ["project " + run["project"]] if run["project"] else []
        run["name"] = ", ".join(shown) or "nothing to check"
    return {"include": runs}


def main():
    files = changed(sys.argv[1] if len(sys.argv) > 1 else "")
    lessons, projects = (ALL, ALL) if files is None else pick(files)
    print(json.dumps(matrix(lessons, projects), ensure_ascii=False))


if __name__ == "__main__":
    main()
