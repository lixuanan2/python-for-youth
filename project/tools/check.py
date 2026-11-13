"""Check the built project module: dist/ is current, holds no answers, and its pages, demos and links are right.

Run in project/ after build.py: python3 tools/check.py   (then tools/verify.py checks the stages themselves)
"""
import ast
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402
import stagefiles as sf  # noqa: E402

ROOT, DIST, LANGUAGE = build.ROOT, build.DIST, build.LANGUAGE
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def check_current():
    """Every file the build makes is on disk as built, and dist/ holds nothing else."""
    files, projects = build.outputs()
    for path, data in files.items():
        assert path.is_file() and path.read_bytes() == data, "Rebuild: python3 tools/build.py (%s)" % path.relative_to(ROOT)
    extra = [p for p in DIST.rglob("*") if p.is_file() and p not in files]
    assert not extra, "Files in dist/ that the build does not make: %s" % [str(p.relative_to(ROOT)) for p in extra]
    decks = {path: data.decode("utf-8") for path, data in files.items() if path.parent.name == "slides"}
    return projects, decks


def check_no_answers(projects):
    """Students get no answer: no answers folder in dist/, and no line of a stage's answer anywhere in dist/ except
    the folders of later stages, which hand earlier answers over on purpose."""
    assert not list(DIST.rglob("answers")), "An answers folder is in dist/"
    for name, proj in projects:
        shipped = [(p, p.read_text(encoding="utf-8")) for p in (DIST / name).rglob("*") if p.suffix in (".py", ".h", ".cpp", ".md", ".html")]
        zipped = [(p, z) for p in (DIST / name).rglob("*.zip") for z in [zipfile.ZipFile(p)]]
        for path, z in zipped:  # a zip holds exactly the stage folders next to it
            for item in z.namelist():
                assert z.read(item) == (DIST / name / "download" / item).read_bytes(), "%s: %s differs from the folder" % (path.name, item)
        handed = {}  # line -> the first stage whose answer has it; from the next stage on it is handed over
        for st in proj.STAGES:
            for fn in st["functions"]:
                for line in fn["py_body"] if LANGUAGE == "python" else fn["cpp_body"]:
                    handed.setdefault(line.strip(), st["id"])
        for st in proj.STAGES:
            for fn in st["functions"]:
                body = fn["py_body"] if LANGUAGE == "python" else fn["cpp_body"]
                for line in body:
                    key = line.strip()
                    first = handed[key]  # a C++ loop head such as for (int i = 0; i < 9; i++) { recurs in later answers
                    if len(key) < 12 or key in ("return False", "return True", "return board", "return '.'", "return -1",
                                                 "return false;", "return true;", "return board;", "return '.';", "return -1;", "return 'X';", "return 'O';"):
                        continue
                    for path, given in shipped:
                        stage = re.search(r"stage(\d+)", str(path.relative_to(DIST)))
                        if stage and int(stage.group(1)) > first:
                            continue  # later stages hand over earlier answers on purpose
                        assert key not in given and html.escape(key) not in given, \
                            "Stage %d answer line in %s: %s" % (st["id"], path.relative_to(ROOT), key)


ALLOWED_IMPORTS = {"unittest", "sys", "os", "json", "threading", "traceback", "webbrowser", "http", "urllib"}  # standard library only; students install nothing


def check_plain(projects):
    """Answers, tests and front ends stay plain: standard library only, and every answer function short."""
    for name, proj in projects:
        files = list((DIST / name / "download").rglob("*.py")) + list((ROOT / name / "answers").rglob("*.py"))
        for path in files if LANGUAGE == "python" else []:
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                found = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
                for module in found:
                    assert module.split(".")[0] in ALLOWED_IMPORTS | {proj.PROJECT["module"]}, "%s imports %s: standard library only" % (path.relative_to(ROOT), module)
        for st in proj.STAGES:
            for fn in st["functions"]:
                # A C++ line that only closes a brace is not a step of the answer, so it does not count.
                body = fn["py_body"] if LANGUAGE == "python" else [line for line in fn["cpp_body"] if line.strip() != "}"]
                assert len(body) <= ANSWER_LINES, "%s %s: the answer is %d lines; keep it short and at the students' level" % (name, fn["name"], len(body))


ANSWER_LINES = 20


def check_needs(projects):
    """Each stage names basics lessons that exist."""
    lessons = {item["id"] for item in json.loads((build.BASICS / "course.json").read_text(encoding="utf-8")) if "id" in item}
    for name, proj in projects:
        assert proj.PROJECT["start"][LANGUAGE] in lessons, "%s: no basics lesson %s" % (name, proj.PROJECT["start"][LANGUAGE])
        for st in proj.STAGES:
            for folder, _ in sf.needs(st, LANGUAGE):
                assert folder in lessons, "%s stage %d needs %s, which basics does not have" % (name, st["id"], folder)


def run_demo(code):
    """Run a demo as the online IDE would: Python as it is, C++ compiled first (a compile error is the error)."""
    if LANGUAGE == "python":
        return subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code], capture_output=True, timeout=10)
    with tempfile.TemporaryDirectory() as scratch:
        exe = Path(scratch) / ("demo.exe" if os.name == "nt" else "demo")
        built = subprocess.run([os.environ.get("CXX", "g++"), "-std=c++11", "-x", "c++", "-", "-o", str(exe)], input=code.encode(), capture_output=True, timeout=60)
        if built.returncode:
            return built
        return subprocess.run([str(exe)], capture_output=True, timeout=10)


def check_demos(decks):
    """A demo prints what its page says it prints, or stops with the error its quiz is about."""
    count = 0
    for path, page in decks.items():
        for n, section in enumerate(re.findall(r"<section id=\"page-\d+\".*?</section>", page, re.S), 1):
            for attrs, body in re.findall(r'<pre class="code"([^>]*\bdata-demo\b[^>]*)>(.*?)</pre>', section, re.S):
                code = "\n".join(text_of(line) for line in re.findall(r'<span class="ln">(.*?)</span>(?=<span class="ln">|$)', body, re.S))
                full = re.search(r'data-full="([^"]*)"', attrs)
                if full:  # a page that shows only some lines gives the whole program, which the IDE gets
                    whole = html.unescape(full.group(1))
                    assert all(line in whole.splitlines() for line in code.splitlines()), "%s page %d: the shown lines are not in data-full" % (path.relative_to(ROOT), n)
                    code = whole
                result = run_demo(code)
                error = re.search(r'data-error="(\w+)"', attrs)
                where = "%s page %d" % (path.relative_to(ROOT), n)
                if error:
                    assert result.returncode and error.group(1) in result.stderr.decode(), "%s: the demo should stop with %s" % (where, error.group(1))
                else:
                    shown = re.search(r"<pre data-out>(.*?)</pre>", section, re.S)
                    assert shown, "%s: a demo needs its output in <pre data-out>" % where
                    assert result.returncode == 0 and result.stdout.decode().replace("\r\n", "\n") == text_of(shown.group(1)) + "\n", \
                        "%s: the demo prints\n%s" % (where, result.stdout.decode() + result.stderr.decode())
                count += 1
    return count


def check_pages(decks):
    """No outside scripts or styles, no labels, and every local link lands on a file in dist/."""
    pages = dict(decks)
    pages.update({p: p.read_text(encoding="utf-8") for p in DIST.rglob("*.html") if p not in decks})
    links = 0
    for path, page in pages.items():
        assert not re.search(r"<(?:script|link)[^>]+(?:src|href)=\"https?:", page), "Outside resource in %s" % path
        assert not re.search(r"必做|选做|课后作业|作业[：:]", text_of(page)), "No 必做, 选做 or 作业 labels: %s" % path
        assert not re.search(r"/Users/|/home/|[A-Za-z]:\\\\", page), "Absolute path in %s" % path
        for quiz in re.findall(r'<div class="quiz.*?</div>', page, re.S):
            right = int(re.search(r'data-right="(\d+)"', quiz).group(1))  # counted from 0, as deck.js reads it
            feedback = re.findall(r'<button[^>]*data-fb="([^"]*)"', quiz)
            assert feedback[right].startswith("答对了"), "%s: the quiz marks button %d right, but its feedback is %s" % (path.relative_to(ROOT), right + 1, feedback[right])
        for href in re.findall(r'href="([^"]+)"', page):
            parts = urlsplit(html.unescape(href))
            if parts.scheme or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            # ../index.html from the module index is the site's home page, which deploy puts there.
            if path == DIST / "index.html" and parts.path.startswith("../"):
                continue
            assert target.is_file(), "Broken link in %s: %s" % (path.relative_to(ROOT), href)
            links += 1
    return links


def main():
    projects, decks = check_current()
    check_no_answers(projects)
    check_plain(projects)
    check_needs(projects)
    demos = check_demos(decks)
    links = check_pages(decks)
    stages = sum(len(p.STAGES) for _, p in projects)
    print("PASS: %d project(s), %d stages, %d decks, %d demos, %d local links; dist/ is current and has no answers." % (len(projects), stages, len(decks), demos, links))


if __name__ == "__main__":
    main()
