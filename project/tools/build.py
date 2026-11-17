"""Build the project module into dist/: the stage folders for the teacher's USB stick, the development document,
one light slide deck per project and the project map.

Run in project/: python3 tools/build.py

Everything about a project lives in its own folder (<project>/stages.py, slides.html, templates/); this file and
template/ are shared by every project. For each project in site.json "projects" it makes:
  dist/<project>/download/stageN/          what students get: their file, the tests, the front end and guide.md
  dist/<project>/download/<project>-stageN.zip, <project>-all.zip   the same folders zipped, for the teacher
  dist/<project>/guide.html                the development document (the same text as every guide.md)
  dist/<project>/slides/index.html         the slides the teacher shows: map, how to test, each stage's functions
  dist/<project>/index.html                the project map
  <project>/answers/stageN/                the teacher's answers; never in dist/
  dist/index.html                          the list of projects

Slides use the basics template, fonts and IDE settings as they are, read from ../basics/ and never changed;
project-only styles are in template/. In <project>/slides.html, <!-- @map -->, <!-- @run --> and <!-- @stage N -->
stand for pages made here from stages.py, so the slides, the development document and the tests agree.
"""
import base64
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASICS = ROOT.parent / "basics"
DIST = ROOT / "dist"
sys.path.insert(0, str(HERE))
import stagefiles as sf  # noqa: E402

SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
LANGUAGE = SITE["language"]
BASICS_SITE = json.loads((BASICS / "site.json").read_text(encoding="utf-8"))
ZIP_TIME = (2026, 1, 1, 0, 0, 0)  # fixed, so a zip changes only when its files do


def esc(text):
    return html.escape(str(text), quote=True).replace("&#x27;", "'")


def code_text(text):
    """`name` in stage data becomes <code>name</code>; **word** becomes <b>word</b>."""
    out = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), esc(text))
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_stages", ROOT / name / "stages.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def basics_read(path):
    return (BASICS / path).read_text(encoding="utf-8")


def font_face(weight):
    data = (BASICS / ("vendor/fonts/jetbrains-mono-latin-%d-normal.woff2" % weight)).read_bytes()
    return ('@font-face{font-family:"JetBrains Mono";font-weight:%d;font-style:normal;'
            'src:url(data:font/woff2;base64,%s) format("woff2")}' % (weight, base64.b64encode(data).decode()))


FONTS = "\n".join(font_face(w) for w in (400, 700, 800))


# ---------------------------------------------------------------- slides: pages made from stages.py

def lesson_link(folder, about):
    return ('<a class="need" href="%s%s/index.html" target="_blank" rel="noopener noreferrer"><b>%s</b><span>%s</span></a>'
            % (esc(SITE["basics"]), esc(folder), esc(folder), esc(about)))


def map_slide(proj):
    rows = "".join('<div class="r d%d" style="grid-template-columns:330px 1fr 560px"><code>第 %d 关</code><span>%s</span><span class="fn">%s</span></div>'
                   % (min(3, 1 + k // 2), st["id"], esc(st["title"]), esc("、".join(sf.fn_names(st))))
                   for k, st in enumerate(proj.STAGES))
    return '''
<!-- map (made by tools/build.py) -->
<section class="slide" aria-label="%s：项目地图" data-chapter="地图">
  <p class="abs r" style="left:96px;top:96px;font:400 36px var(--code);color:var(--muted)"># 项目课 · %s</p>
  <h2 class="abs r" style="left:96px;top:160px;font:800 96px/1.2 var(--text)">%s：%d 关</h2>
  <div class="sheet3 route" style="top:330px">%s</div>
  <p class="abs say r d3" style="left:96px;top:900px;width:1728px;color:var(--muted)">每关写一两个函数，名字照开发文档写。测试全过，就进下一关。</p>
  <div class="foot"></div>
</section>
''' % (esc(proj.PROJECT["title"]), esc(proj.PROJECT["title"]), esc(proj.PROJECT["title"]), len(proj.STAGES), rows)


EDITORS = {"python": "PyCharm、VS Code", "cpp": "Dev-C++、VS Code"}
# Step 2 and step 3 of the run page: how to run a test file and how to read its last line, per language.
RUN_STEPS = {"python": ("运行 test_stageN：PyCharm 右键 → Run，VS Code 点 ▶", "OK 就是全过；FAILED 就往上找 FAIL"),
             "cpp": ("编译运行 test_stageN.cpp：Dev-C++ 按 F11", "“通过 8 / 8”就是全过；没全过就往上找 [错]")}


def run_slide(proj, result):
    failures, excerpt = result
    test = sf.names(LANGUAGE, proj, 1)[1]
    return '''
<!-- run the tests (made by tools/build.py) -->
<section class="slide" aria-label="运行测试" data-chapter="测试">
  <h2 class="t r">每关写完，就运行测试</h2>
  <div class="steps3">
    <div class="r d1"><i>1</i><b>打开文件夹</b><span>用编辑器打开这一关的 stageN 文件夹</span></div>
    <div class="r d2"><i>2</i><b>运行测试</b><span>%s</span></div>
    <div class="r d3"><i>3</i><b>看最后一行</b><span>%s</span></div>
  </div>
  <div class="slip r d3" style="left:96px;top:690px;width:1728px"><small>第 1 关还没写就运行 %s，是这样的（%d 条没过；中间省掉了一些行）</small><pre style="font-size:28px;line-height:1.45">%s</pre></div>
  <div class="foot"></div>
</section>
''' % (RUN_STEPS[LANGUAGE] + (esc(test), failures, esc("\n".join(excerpt))))


def stage_title(proj, st):
    n = st["id"]
    needs = "".join(lesson_link(f, a) for f, a in sf.needs(st, LANGUAGE))
    return '''
<!-- stage %d (made by tools/build.py) -->
<section class="slide dark" data-stage="%d" aria-label="第 %d 关：%s" data-chapter="第 %d 关">
  <p class="abs r" style="left:96px;top:96px;font:400 36px var(--code);color:var(--ghost)"># %s · 第 %d 关 / 共 %d 关</p>
  <h2 class="abs r d1" style="left:96px;top:170px;font:800 110px/1.2 var(--text)">%s</h2>
  <p class="abs r d1" style="left:96px;top:330px;width:1728px;font:700 44px/1.5 var(--text)">%s</p>
  <p class="abs r d2" style="left:96px;top:450px;font:400 32px var(--text);color:var(--ghost)">要先学完（点开是基础课件，要联网）：</p>
  <div class="needs r d2" style="top:510px">%s</div>
  <div class="foot"></div>
</section>
''' % (n, n, n, esc(st["title"]), n, esc(proj.PROJECT["title"]), n, len(proj.STAGES), esc(st["title"]), esc(st["goal"]), needs)


SPEC_LINES = 5  # more than this and the hints get a page of their own


def spec_pages(fn):
    sig, plain, examples = sf.spec(fn, LANGUAGE)
    hints = [line for line in plain if line.startswith("提示：")] if len(plain) > SPEC_LINES else []
    plain = [line for line in plain if line not in hints]
    rows = "".join("<li>%s</li>" % code_text(line) for line in plain)
    shown = "".join('<li><code>%s</code>%s</li>' % (esc(call), esc(note.lstrip("："))) for call, note in examples)
    out = '''
<!-- spec: %s (made by tools/build.py) -->
<section class="slide" aria-label="要写的函数：%s">
  <h2 class="t r">要写的函数：<span style="font-family:var(--code)">%s</span></h2>
  <div class="sig r d1"><small>名字和参数必须照写，测试按这个名字检查</small><code>%s</code></div>
  <ul class="spec r d2">%s</ul>
  <div class="examples r d3"><small>例子</small><ul>%s</ul></div>
  <div class="foot"></div>
</section>
''' % (fn["name"], esc(fn["name"]), esc(fn["name"]), esc(sig), rows, shown)
    if hints:
        out += '''
<!-- spec hints: %s (made by tools/build.py) -->
<section class="slide" aria-label="%s 的提示">
  <h2 class="t r"><span style="font-family:var(--code)">%s</span> 的提示</h2>
  <ul class="spec wide r d1">%s</ul>
  <div class="foot"></div>
</section>
''' % (fn["name"], esc(fn["name"]), esc(fn["name"]), "".join("<li>%s</li>" % code_text(h[3:]) for h in hints))
    return out


def thanks(proj):
    return '''
<!-- made by tools/build.py -->
<section class="slide dark thanks" aria-label="谢谢">
  <h2 class="abs r" style="left:96px;top:130px;font:800 200px/1.2 var(--text)">一关一关来！</h2>
  <p class="abs say r d1" style="left:96px;top:470px;font-size:52px">%s的 %d 关都在开发文档里，测试全过就进下一关。</p>
  <a class="go-next r d2" style="top:620px" href="../index.html">回到项目地图</a>
</section>
''' % (esc(proj.PROJECT["title"]), len(proj.STAGES))


def write_stage(files, folder):
    """Put one stage's files in a folder, as students get them (pictures go in their own subfolder)."""
    for file, data in files.items():
        path = Path(folder) / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(sf.as_bytes(data))


def cpp_starter_result(proj, folder, st, test):
    """C++: compile the untouched starter with its test (g++, or CXX) and keep the first [错] with its two lines and the end."""
    with tempfile.TemporaryDirectory() as scratch:
        write_stage(sf.stage_files(proj, folder, st, LANGUAGE), scratch)
        exe = Path(scratch) / ("test.exe" if os.name == "nt" else "test")
        built = subprocess.run([os.environ.get("CXX", "g++"), test, "-o", str(exe)], cwd=scratch, capture_output=True, timeout=120)
        assert built.returncode == 0, "stage %d: the starter does not compile\n%s" % (st["id"], built.stderr.decode("utf-8", "replace")[-500:])
        out = subprocess.run([str(exe)], cwd=scratch, capture_output=True, timeout=60).stdout.decode("utf-8")
    lines = out.replace("\r\n", "\n").splitlines()
    wrong = [k for k, line in enumerate(lines) if line.startswith("[错]")]
    assert wrong, "stage %d: the starter's tests do not fail\n%s" % (st["id"], out[-500:])
    return len(wrong), lines[wrong[0]:wrong[0] + 3] + lines[-2:]


def starter_result(proj, folder, st):
    """How many tests the untouched starter fails, and real lines of what the student sees, from a scratch copy."""
    test = sf.names(LANGUAGE, proj, st["id"])[1]
    if LANGUAGE == "cpp":
        return cpp_starter_result(proj, folder, st, test)
    with tempfile.TemporaryDirectory() as scratch:
        write_stage(sf.stage_files(proj, folder, st, LANGUAGE), scratch)
        out = subprocess.run([sys.executable, "-B", "-X", "utf8", test], cwd=scratch, capture_output=True, timeout=60).stderr.decode("utf-8")
    found = re.search(r"FAILED \(failures=(\d+)\)", out)
    assert found, "stage %d: the starter's tests do not fail cleanly\n%s" % (st["id"], out[-500:])
    lines = out.splitlines()
    fail = next(k for k, line in enumerate(lines) if line.endswith("... FAIL"))
    error = next(line for line in lines if line.startswith("AssertionError:"))
    return int(found.group(1)), [lines[fail - 1], lines[fail], error, found.group(0)]


KEYWORDS = {"python": r"\b(?:def|return|if|elif|else|for|while|in|and|or|not|True|False|None)\b",
            "cpp": r"\b(?:int|char|bool|string|return|if|else|for|while|true|false|using|namespace)\b"}
TOKEN = r"(?P<s>'[^']*'|\"[^\"]*\")|(?P<m>\b\d+\b)|(?P<f>\b\w+(?=\())|(?P<k>%s)"


def highlight(code):
    """Demo code as the basics editor shows it: one .ln per line, with the same colour classes."""
    token = re.compile(TOKEN % KEYWORDS[LANGUAGE])

    def line(text):
        out, at = [], 0
        for m in token.finditer(text):
            out.append(esc(text[at:m.start()]))
            out.append('<span class="%s">%s</span>' % (m.lastgroup, esc(m.group())))
            at = m.end()
        return '<span class="ln">%s</span>' % "".join(out + [esc(text[at:])])
    return "".join(line(l) for l in html.unescape(code).split("\n"))


# <!-- @answers N --> in slides.html: after a stage is taught and done, one page per function with its reference answer,
# straight from stages.py (the same source as answers/). It opens covered; the teacher turns the next step to show it.
# A function with "reveal" shows its body a group of lines at a time, each with its rule.
def answer_pages(proj, st):
    lang = "py" if LANGUAGE == "python" else "cpp"
    pages = []
    for fn in st["functions"]:
        # A language whose answer reads differently has its own words and line groups (cpp_say, cpp_reveal).
        reveal = fn.get(lang + "_reveal", fn.get("reveal") if lang == "py" else None)
        body = fn[lang + "_body"]
        groups = reveal or [("", len(body))]  # the answer's own lines; C++'s closing } comes after them
        assert sum(n for _, n in groups) == len(body), "%s: reveal must cover the answer's lines" % fn["name"]
        # Lines of each group in order; the signature goes before the first group, C++'s closing } after the last.
        chunks, at = [], 0
        for k, (label, n) in enumerate(groups):
            chunks.append((k, label, body[at:at + n]))
            at += n
        sig, close = fn[lang + "_sig"], ([] if lang == "py" else ["}"])
        # A long revealed answer (C++'s braces make it longer) goes on as many pages as it needs, a group or more each.
        parts = [chunks] if not reveal or reveal_size(sig, chunks, close, True, True) >= 24 else split_groups(sig, chunks, close)
        shown = 0
        for p_index, part in enumerate(parts):
            first, last = p_index == 0, p_index == len(parts) - 1
            code = ([sig] if first else []) + [line for _, _, lines in part for line in lines] + (close if last else [])
            base = 2 if first else 1  # the first page opens covered (step 1); a page that goes on opens with its first group
            step = ([2] if first else []) + [base + j for j, (_, _, lines) in enumerate(part) for _ in lines] + ([base + len(part) - 1] if last and close else [])
            widest = max(len(line) for line in code)
            # Beside a column for the rules when the lines are short; full width with the words underneath when they
            # are long, unless that makes the code no bigger.
            size, width, top = min(44, int(1024 / (0.6 * widest)), int(650 / (1.55 * len(code)))), 1180, 200
            side = "left:1340px;top:220px;width:484px"
            if reveal:  # a long answer shown a rule at a time: every line of the editor's height counts
                size, top = reveal_size(sig, part, close, first, last), 180
            elif size < 30:
                wide = min(44, int(1572 / (0.6 * widest)), int(530 / (1.55 * len(code))))
                if wide > size:
                    size, width, side = wide, 1728, "left:96px;top:880px;width:1728px"
            assert size >= 24, "%s: the answer is too long for one page" % fn["name"]
            lines = "".join(highlight(line).replace('<span class="ln">', '<span class="ln step s%d">' % k, 1) for line, k in zip(code, step))
            rules = "".join('<p class="say step s%d" style="margin-bottom:18px"><b>%d</b>　%s</p>' % (base + j, k + 1, esc(label))
                            for j, (k, label, _) in enumerate(part) if label)
            steps = base + len(part) - 1
            title = esc(fn["name"]) + ("" if first else "（接上页）")
            cover = ('<div class="abs only1" style="left:96px;top:330px;width:1728px;text-align:center"><p class="say" style="font-size:64px;font-weight:800">'
                     '先自己做完，再翻开对一对</p><p class="say" style="color:var(--ghost);margin-top:24px">讲的时候按 → 翻开</p></div>') if first else ""
            say = '<p class="say step s%d" style="color:var(--ghost);font-size:34px">%s</p>' % (steps, code_text(fn.get(lang + "_say", fn["say"]))) if last else ""
            pages.append('''
<!-- answer: %s (made by tools/build.py) -->
<section class="slide dark" aria-label="参考答案：%s" data-answer="%s" data-steps="%d" data-at="%d">
  <h2 class="t">参考答案：<span style="font-family:var(--code)">%s</span></h2>
  %s
  <div class="editor%s" style="left:96px;top:%dpx;width:%dpx;--fs:%dpx"><div class="tab">%s</div>
<pre class="code"%s>%s</pre></div>
  <div class="abs" style="%s">%s%s</div>
  <div class="foot"></div>
</section>
''' % (fn["name"], title, fn["name"] if first else "%s-%d" % (fn["name"], p_index + 1), steps, steps, title, cover,
           " step s2" if first else "", top, width, size, esc(sf.names(LANGUAGE, proj, st["id"])[0]),
           "" if first else ' style="counter-reset:ln %d"' % shown, lines, side, rules, say))
            shown += len(code)
    return "".join(pages)


def reveal_size(sig, part, close, first, last):
    """The code size for a revealed answer page holding these groups."""
    code = ([sig] if first else []) + [line for _, _, lines in part for line in lines] + (close if last else [])
    return min(44, int(1024 / (0.6 * max(len(line) for line in code))), int(690 / (1.55 * len(code))))


def split_groups(sig, chunks, close):
    """Groups packed onto as few pages as keep the code at 24px or more."""
    parts = [[]]
    for chunk in chunks:
        if parts[-1] and reveal_size(sig, parts[-1] + [chunk], close, len(parts) == 1, chunk is chunks[-1]) < 24:
            parts.append([])
        parts[-1].append(chunk)
    return parts


def slides(proj, name):
    text = (ROOT / name / "slides.html").read_text(encoding="utf-8")
    made = {"map": map_slide(proj), "run": run_slide(proj, starter_result(proj, ROOT / name, proj.STAGES[0]))}
    made.update({"stage %d" % st["id"]: stage_title(proj, st) + "".join(spec_pages(fn) for fn in st["functions"]) for st in proj.STAGES})
    made.update({"answers %d" % st["id"]: answer_pages(proj, st) for st in proj.STAGES})
    for key, page in made.items():
        assert text.count("<!-- @%s -->" % key) == 1, "%s: slides.html needs <!-- @%s --> once" % (name, key)
        text = text.replace("<!-- @%s -->" % key, page.strip())
    text = re.sub(r'(<pre class="code"[^>]*\bdata-demo\b[^>]*>)(.*?)(</pre>)', lambda m: m.group(1) + highlight(m.group(2)) + m.group(3), text, flags=re.S)
    count = 0

    def number(match):
        nonlocal count
        count += 1
        return '<section id="page-%d" class="slide%s' % (count, " active visible" if count == 1 else "")
    return re.sub(r'<section class="slide', number, text.rstrip() + "\n" + thanks(proj))


def render_deck(proj, name):
    css = "\n".join([FONTS, basics_read("vendor/viewport.css"), basics_read("template/theme.css"),
                     (ROOT / "template" / "project.css").read_text(encoding="utf-8")])
    script = basics_read("template/deck.js").replace("{{ide}}", json.dumps(BASICS_SITE["ide"], ensure_ascii=False)).replace("{{language}}", LANGUAGE)
    page = basics_read("template/page.html")
    fields = dict(title=esc(proj.PROJECT["title"]), lesson=json.dumps("项目 " + proj.PROJECT["title"], ensure_ascii=False), css=css, site=esc(SITE["title"]),
                  slides=slides(proj, name).rstrip(), script=script.rstrip())
    for key, value in fields.items():
        page = page.replace("{{" + key + "}}", value)
    return page.replace("<!-- Generated by tools/build.py. Edit lessons/ and template/, not this file. -->",
                        "<!-- Generated by project/tools/build.py. Edit project/, not this file. -->")


def stage_pages(deck):
    """The page each stage starts on in the deck, for links straight to it."""
    return {int(n): int(page) for page, n in re.findall(r'<section id="page-(\d+)" class="slide[^"]*" data-stage="(\d+)"', deck)}


# ---------------------------------------------------------------- the development document as a web page

def markdown_html(text):
    """The small part of Markdown the development document uses: headings, paragraphs, lists, tables, code blocks."""
    out, para, items, table, code = [], [], [], [], None

    def flush():
        if para:
            out.append("<p>%s</p>" % code_text(" ".join(para)))
            para.clear()
        if items:
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % code_text(i) for i in items))
            items.clear()
        if table:
            head, rows = table[0], table[2:]
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                "".join("<th>%s</th>" % code_text(c) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % code_text(c) for c in r) for r in rows)))
            table.clear()

    for line in text.split("\n"):
        if code is not None:
            if line.startswith("```"):
                out.append("<pre>%s</pre>" % esc("\n".join(code)))
                code = None
            else:
                code.append(line)
            continue
        if line.startswith("```"):
            flush()
            code = []
        elif line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            stage = re.match(r"第 (\d+) 关", title)
            out.append('<h%d%s>%s</h%d>' % (level, ' id="stage-%s"' % stage.group(1) if stage and level == 2 else "", code_text(title), level))
        elif line.startswith("| "):
            if para or items:
                flush()
            table.append([c.strip() for c in line.strip("|").split("|")])
        elif line.startswith("- "):
            if para or table:
                flush()
            items.append(line[2:])
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    flush()
    return "\n".join(out)


def render_guide(proj, name):
    body = '''
<header class="hero"><div class="in">
  <nav class="crumbs"><a href="index.html">← 项目地图</a></nav>
  <p class="lead small">每关的文件夹里都有这一份，叫 <code>guide.md</code>。</p>
</div></header>
<main class="doc">
%s
</main>
''' % markdown_html(sf.dev_doc(proj, LANGUAGE))
    return page_shell("%s：开发文档 · %s" % (proj.PROJECT["title"], SITE["title"]), body)


# ---------------------------------------------------------------- map and index pages

def given_and_back(fn):
    lines = sf.spec(fn, LANGUAGE)[1]
    pick = lambda head: next((l.split("：", 1)[1] for l in lines if l.startswith(head)), "")
    return pick("给它"), pick("还给你")


def render_map(proj, name, pages):
    stages = []
    for st in proj.STAGES:
        n = st["id"]
        fns = "".join("<code>%s</code>" % esc(fn["name"]) for fn in st["functions"])
        needs = "".join('<a href="%s%s/index.html">%s</a>' % (esc(SITE["basics"]), esc(f), esc(f)) for f, _ in sf.needs(st, LANGUAGE))
        stages.append('''<li><div class="n">%d</div><div><h3>%s</h3><p>%s</p><p class="fns">要写：%s</p><p class="needs">先学完：%s</p></div>
<nav aria-label="第 %d 关"><a class="go" href="guide.html#stage-%d">开发文档</a><a href="slides/index.html#page-%d">放映这一关</a><a href="download/%s-stage%d.zip" download>下载 zip</a></nav></li>'''
                      % (n, esc(st["title"]), esc(st["goal"]), fns, needs, n, n, pages[n], name, n))
    table = "".join("<tr><td><code>%s</code></td><td>%d</td><td>%s</td><td>%s</td></tr>" % ((esc(fn["name"]), st["id"]) + tuple(code_text(x) for x in given_and_back(fn)))
                    for st in proj.STAGES for fn in st["functions"])
    me = sf.names(LANGUAGE, proj, 1)
    body = '''
<header class="hero"><div class="in">
  <nav class="crumbs"><a href="../index.html">← 项目课</a></nav>
  <h1>%s</h1>
  <p class="lead">%s</p>
  <p class="lead small">从基础课件 <a href="%s%s/index.html">%s</a> 学完就能开始。代码在自己的电脑上写和运行，编辑器不限（%s 都行）。</p>
  <div class="actions"><a class="start" href="guide.html">▶ 打开开发文档</a><a class="second" href="slides/index.html">放映课件</a><a class="second" href="download/%s-all.zip" download>⬇ 下载全部 %d 关（zip）</a></div>
</div></header>
<main>
  <section><h2>项目地图</h2><ol class="route">%s</ol></section>
  <section><h2>函数一览</h2><p>名字必须照写：老师的测试按这些名字检查。</p>
    <table><thead><tr><th>函数</th><th>关</th><th>给它</th><th>还给你</th></tr></thead><tbody>%s</tbody></table></section>
  <section><h2>给老师：准备 U 盘</h2><ol class="plain">
    <li>下载全部关卡的 zip，在电脑上解压。</li>
    <li>把解压出来的 <code>stage1</code> 到 <code>stage%d</code> 文件夹拷进 U 盘。拷文件夹本身，不要只拷 zip：在 zip 里直接运行会找不到同一个文件夹里的文件。</li>
    <li>每个文件夹里都有开发文档 <code>guide.md</code>，和这个网站上的开发文档一样。</li>
    <li>参考答案不在下载包里，在仓库的 <code>project/%s/answers/</code>，不要拷给学生。</li>
    <li>学生用编辑器打开某一关的文件夹，改 <code>%s</code>，运行 <code>test_stageN</code> 检查，全过以后运行 <code>%s</code> 玩。</li>
  </ol></section>
</main>
''' % (esc(proj.PROJECT["title"]), esc(proj.PROJECT["lead"]), esc(SITE["basics"]), esc(proj.PROJECT["start"][LANGUAGE]), esc(proj.PROJECT["start"][LANGUAGE]),
       EDITORS[LANGUAGE], name, len(proj.STAGES), "\n".join(stages), table, len(proj.STAGES), name, esc(me[0]), esc(me[2]))
    return page_shell("%s · %s" % (proj.PROJECT["title"], SITE["title"]), body)


def render_index(projects):
    cards = "".join('<li><div class="n">%d</div><div><h3>%s</h3><p>%s</p><p class="needs">学完 %s 就能开始，一共 %d 关。</p></div><nav><a class="go" href="%s/index.html">打开项目地图</a></nav></li>'
                    % (k, esc(p.PROJECT["title"]), esc(p.PROJECT["lead"]), esc(p.PROJECT["start"][LANGUAGE]), len(p.STAGES), name)
                    for k, (name, p) in enumerate(projects, 1))
    body = '''
<header class="hero"><div class="in">
  <nav class="crumbs"><a href="../index.html">← 课程首页</a><a href="../basics/index.html">基础课件</a></nav>
  <h1>项目课</h1>
  <p class="lead">学完基础课件的一部分，就能做一个分关卡的小项目：老师给好画面和测试，你只写程序的逻辑，一关一关做到能玩。</p>
  <p class="lead small">%s</p>
</div></header>
<main><section><h2>项目</h2><ol class="route">%s</ol></section></main>
''' % (esc(SITE["footer"]), cards)
    return page_shell(SITE["title"], body)


def page_shell(title, body):
    css = (ROOT / "template" / "site.css").read_text(encoding="utf-8")
    return '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<!-- Generated by project/tools/build.py. Edit project/, not this file. -->
<style>
%s
%s
</style>
</head>
<body>
%s
<footer>%s</footer>
</body>
</html>
''' % (esc(title), FONTS, css, body.strip(), esc(SITE["footer"]))


# ---------------------------------------------------------------- writing

def zip_bytes(folders):
    """A zip of {folder name: {file: text}}: stored, not compressed, so it is the same bytes on every system."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for folder, files in folders.items():
            for file in sorted(files):
                info = zipfile.ZipInfo("%s/%s" % (folder, file), ZIP_TIME)
                info.external_attr = 0o644 << 16
                z.writestr(info, sf.as_bytes(files[file]))
    return out.getvalue()


def outputs():
    """Every file the build writes: {path: bytes}. check.py compares these with what is on disk."""
    files, projects = {}, []
    for name in SITE["projects"]:
        proj = load(name)
        projects.append((name, proj))
        folders = {}
        for st in proj.STAGES:
            n = st["id"]
            stage = sf.stage_files(proj, ROOT / name, st, LANGUAGE)
            folders["stage%d" % n] = stage
            for file, data in stage.items():
                files[DIST / name / "download" / ("stage%d" % n) / file] = sf.as_bytes(data)
            files[DIST / name / "download" / ("%s-stage%d.zip" % (name, n))] = zip_bytes({"stage%d" % n: stage})
            files[ROOT / name / "answers" / ("stage%d" % n) / sf.names(LANGUAGE, proj, n)[0]] = sf.answer_file(proj, st, LANGUAGE).encode("utf-8")
        files[DIST / name / "download" / ("%s-all.zip" % name)] = zip_bytes(folders)
        deck = render_deck(proj, name)
        files[DIST / name / "slides" / "index.html"] = deck.encode("utf-8")
        for picture in sorted((ROOT / name / "slide-images").glob("*.png")):  # pictures the deck shows, next to it
            files[DIST / name / "slides" / picture.name] = picture.read_bytes()
        files[DIST / name / "guide.html"] = render_guide(proj, name).encode("utf-8")
        files[DIST / name / "index.html"] = render_map(proj, name, stage_pages(deck)).encode("utf-8")
    files[DIST / "index.html"] = render_index(projects).encode("utf-8")
    return files, projects


def main():
    files, projects = outputs()
    for name, _ in projects:
        shutil.rmtree(DIST / name, ignore_errors=True)
        shutil.rmtree(ROOT / name / "answers", ignore_errors=True)
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print("Built %d project(s): stage folders, development document, slides and map into dist/" % len(projects))


if __name__ == "__main__":
    main()
