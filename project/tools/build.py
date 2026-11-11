"""Build the project module into dist/: stage folders for the teacher's USB stick, zips, slides and the project map.

Run in project/: python3 tools/build.py

For each project in site.json "projects" (a folder with stages.py, slides/, templates/):
  dist/<project>/download/stageN/         what students get: their file, the tests, the front end, guide.md
  dist/<project>/download/<project>-stageN.zip, <project>-all.zip   the same folders zipped, for the teacher
  dist/<project>/stageN/index.html        the slides for that stage
  dist/<project>/index.html               the project map
  <project>/answers/stageN/               the teacher's answers; never in dist/
  dist/index.html                         the list of projects

Slides use the basics template, fonts and IDE settings as they are, read from ../basics/ and never changed;
project-only styles are in template/. In slides/stageN.html, <!-- @cover --> and the other markers stand for pages
made here from stages.py, so the slides, the guide and the tests tell the same names and examples.
"""
import base64
import html
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
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
    return html.escape(str(text), quote=True)


def code_text(text):
    """`name` in stage data becomes <code>name</code>."""
    return re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % esc(m.group(1)), esc(text).replace("&#x27;", "'"))


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


# ---------------------------------------------------------------- generated pages

def lesson_link(folder, about):
    return ('<a class="need" href="%s%s/index.html" target="_blank" rel="noopener noreferrer"><b>%s</b><span>%s</span></a>'
            % (esc(SITE["basics"]), esc(folder), esc(folder), esc(about)))


def board_html(board="", numbers=True):
    cells = []
    for i in range(9):
        mark = board[i] if board and board[i] != "." else ""
        cells.append('<i class="%s">%s</i>' % ("x" if mark == "X" else "o" if mark == "O" else "", mark or (str(i) if numbers else "")))
    return '<div class="ttt">%s</div>' % "".join(cells)


def cover(proj, st):
    n, last = st["id"], len(proj.STAGES)
    return '''
<!-- cover (made by tools/build.py) -->
<section class="slide" aria-label="第 %d 关：%s" data-chapter="开始">
  <p class="abs r" style="left:96px;top:96px;font:400 36px var(--code);color:var(--muted)"># %s · 第 %d 关 / 共 %d 关</p>
  <h1 class="abs r d1" style="left:96px;top:230px;width:1100px;font:800 140px/1.2 var(--text)">%s</h1>
  <p class="abs r d2" style="left:96px;top:600px;width:1060px;font:700 46px/1.5 var(--text)">%s</p>
  <p class="abs say r d3" style="left:96px;top:800px;width:1060px;color:var(--muted)">做完以后：%s</p>
  <div class="abs r d1" style="left:1290px;top:230px">%s</div>
  <div class="foot"></div>
</section>
''' % (n, esc(st["title"]), esc(proj.PROJECT["title"]), n, last, esc(st["title"]), esc(st["goal"]), code_text(proj.PLAY_NOTES[n]), board_html())


def review(proj, st):
    links = "".join(lesson_link(f, a) for f, a in sf.needs(st, LANGUAGE))
    return '''
<!-- review (made by tools/build.py) -->
<section class="slide" aria-label="先复习" data-chapter="先复习">
  <h2 class="t r">这一关要用到的基础课</h2>
  <div class="needs r d1">%s</div>
  <p class="abs say r d2" style="left:96px;top:880px;width:1728px;color:var(--muted)">哪一课忘了，就点开再看一遍。基础课件在网上，点开要联网。</p>
  <div class="foot"></div>
</section>
''' % links


SPEC_LINES = 5  # more than this and the hints get a page of their own


def spec_page(proj, st, fn):
    sig, plain, examples = sf.spec(fn, LANGUAGE)
    hints = [line for line in plain if line.startswith("提示：")] if len(plain) > SPEC_LINES else []
    plain = [line for line in plain if line not in hints]
    rows = "".join("<li>%s</li>" % code_text(line) for line in plain)
    shown = "".join('<li><code>%s</code>%s</li>' % (esc(call), esc(note.lstrip("："))) for call, note in examples)
    return '''
<!-- spec: %s (made by tools/build.py) -->
<section class="slide" aria-label="要写的函数：%s" data-chapter="规格">
  <h2 class="t r">要写的函数：<span style="font-family:var(--code)">%s</span></h2>
  <div class="sig r d1"><small>名字和参数必须照写，测试按这个名字检查</small><code>%s</code></div>
  <ul class="spec r d2">%s</ul>
  <div class="examples r d3"><small>例子</small><ul>%s</ul></div>
  <div class="foot"></div>
</section>
''' % (fn["name"], esc(fn["name"]), esc(fn["name"]), esc(sig), rows, shown) + ("" if not hints else '''
<!-- spec hints: %s (made by tools/build.py) -->
<section class="slide" aria-label="%s 的提示">
  <h2 class="t r"><span style="font-family:var(--code)">%s</span> 的提示</h2>
  <ul class="spec wide r d1">%s</ul>
  <div class="foot"></div>
</section>
''' % (fn["name"], esc(fn["name"]), esc(fn["name"]), "".join("<li>%s</li>" % code_text(h[3:]) for h in hints)))


def folder_page(proj, name, st):
    n = st["id"]
    me, test, play = sf.names(LANGUAGE, proj, n)
    rows = [(me, "你", "只改最下面“第 %d 关：你来写”%s" % (n, "；上面是前几关的答案" if n > 1 else "")),
            (test, "老师", "检查你写对没有"), (play, "老师", "测试全过以后用来玩"), ("guide.md", "老师", "这一关的引导文档")]
    if LANGUAGE == "cpp":
        rows.insert(2, ("check.h", "老师", "测试用的小工具"))
    table = "".join('<div class="%s"><code>%s</code><b>%s</b><span>%s</span></div>' % ("mine" if who == "你" else "", esc(f), who, esc(what))
                    for f, who, what in rows)
    return '''
<!-- folder (made by tools/build.py) -->
<section class="slide" aria-label="第 %d 关的文件夹" data-chapter="文件夹">
  <h2 class="t r">U 盘里的 stage%d 文件夹</h2>
  <div class="files r d1">%s</div>
  <p class="abs say r d2" style="left:96px;top:780px;width:1000px">用编辑器打开整个 <code>stage%d</code> 文件夹（PyCharm、VS Code 都行），只改 <code>%s</code>。</p>
  <a class="dl r d3" href="../download/%s-stage%d.zip" download>⬇ 老师下载这一关（zip）</a>
  <div class="foot"></div>
</section>
''' % (n, n, table, n, esc(me), name, n)


def run_page(proj, st, result):
    n = st["id"]
    me, test, play = sf.names(LANGUAGE, proj, n)
    failures, excerpt = result
    return '''
<!-- run the tests (made by tools/build.py) -->
<section class="slide" aria-label="运行测试" data-chapter="测试">
  <h2 class="t r">写完就运行测试</h2>
  <div class="steps3">
    <div class="r d1"><i>1</i><b>打开测试</b><span>在编辑器里打开 %s</span></div>
    <div class="r d2"><i>2</i><b>运行</b><span>PyCharm 右键 → Run，VS Code 点右上角的 ▶</span></div>
    <div class="r d3"><i>3</i><b>看最后一行</b><span>OK 就是全过；FAILED 就往上找 FAIL</span></div>
  </div>
  <div class="slip r d3" style="left:96px;top:690px;width:1728px"><small>还没写就运行，是这样的（%d 条测试，%d 条没过；中间省掉了一些行）</small><pre style="font-size:28px;line-height:1.45">%s</pre></div>
  <div class="foot"></div>
</section>
''' % (esc(test), len(st["tests"]), failures, esc("\n".join(excerpt)))


def play_page(proj, st):
    n = st["id"]
    me, test, play = sf.names(LANGUAGE, proj, n)
    ch = proj.CHALLENGES[n]
    if ch.startswith("PY: "):
        ch = ch.split("|")[0][4:] if LANGUAGE == "python" else ch.split("|")[1][5:]
    return '''
<!-- play and think (made by tools/build.py) -->
<section class="slide" aria-label="接上前端玩" data-chapter="玩">
  <div class="band r"><b>测试<br>全过了</b><span>运行 %s，玩一玩你写的函数。</span></div>
  <div class="turn">
    <h2 class="r d1">接上前端玩</h2>
    <p class="say r d1">%s</p>
    <p class="say r d2" style="margin-top:36px"><b>想一想：</b>%s</p>
  </div>
  <div class="foot"></div>
</section>
''' % (esc(play), code_text(proj.PLAY_NOTES[n]), esc(ch))


def tell_page(proj, st):
    fns = "、".join(st["functions"][k]["name"] for k in range(len(st["functions"])))
    return '''
<!-- tell (made by tools/build.py) -->
<section class="slide olive" aria-label="讲一讲" data-steps="3" data-at="1" data-chapter="讲一讲">
  <h2 class="t r">讲一讲你的 <span style="font-family:var(--code)">%s</span></h2>
  <div class="hints">
    <p><i>1</i><span>给它什么、还给你什么？用一句话说。</span></p>
    <p class="step s2"><i>2</i><span>你最先写的是哪一句？为什么先写它？</span></p>
    <p class="step s3"><i>3</i><span>哪一条测试最难过？你是怎么发现错在哪里的？</span></p>
  </div>
  <div class="foot"></div>
</section>
''' % esc(fns)


def thanks(proj, name, st):
    n, last = st["id"], len(proj.STAGES)
    onward = ('<a class="go-next r d3" href="../stage%d/index.html">下一关：%s</a>' % (n + 1, esc(proj.STAGES[n]["title"])) if n < last
              else '<p class="abs say r d3 next-note">%s全部 %d 关做完了，了不起！</p>' % (esc(proj.PROJECT["title"]), last))
    return '''
<!-- made by tools/build.py -->
<section class="slide dark thanks" aria-label="这一关完成">
  <h2 class="abs r" style="left:96px;top:130px;font:800 200px/1.2 var(--text)">第 %d 关完成！</h2>
  <p class="abs say r d1" style="left:96px;top:470px;font-size:52px">测试全过，就可以进下一关了。</p>
  <a class="go-next r d2" style="top:620px" href="../index.html">回到项目地图</a>
  %s
</section>
''' % (n, onward)


def starter_failures(proj, name, st):
    """How many tests the untouched starter fails, and real lines of what the student sees (Python; C++ to come)."""
    folder = DIST / name / "download" / ("stage%d" % st["id"])
    test = sf.names(LANGUAGE, proj, st["id"])[1]
    if LANGUAGE != "python":
        return 0, []
    out = subprocess.run([sys.executable, "-X", "utf8", test], cwd=folder, capture_output=True, timeout=60).stderr.decode("utf-8")
    found = re.search(r"FAILED \(failures=(\d+)\)", out)
    assert found, "%s stage %d: the starter's tests do not fail cleanly\n%s" % (name, st["id"], out[-500:])
    lines = out.splitlines()
    fail = next(k for k, line in enumerate(lines) if line.endswith("... FAIL"))
    error = next(line for line in lines if line.startswith("AssertionError:"))
    return int(found.group(1)), [lines[fail - 1], lines[fail], error, found.group(0)]


KEYWORDS = {"python": r"\b(?:def|return|if|elif|else|for|while|in|and|or|not|True|False|None)\b",
            "cpp": r"\b(?:int|char|bool|string|return|if|else|for|while|true|false|using|namespace)\b"}
TOKEN = re.compile(r"(?P<s>'[^']*'|\"[^\"]*\")|(?P<m>\b\d+\b)|(?P<f>\b\w+(?=\())|(?P<k>%s)")


def highlight(code):
    """Demo code as the basics editor shows it: one .ln per line, with the same colour classes."""
    token = re.compile(TOKEN.pattern % KEYWORDS[LANGUAGE])

    def line(text):
        out, at = [], 0
        for m in token.finditer(text):
            out.append(esc(text[at:m.start()]).replace("&#x27;", "'"))
            out.append('<span class="%s">%s</span>' % (m.lastgroup, esc(m.group()).replace("&#x27;", "'")))
            at = m.end()
        out.append(esc(text[at:]).replace("&#x27;", "'"))
        return '<span class="ln">%s</span>' % "".join(out)
    return "".join(line(l) for l in html.unescape(code).split("\n"))


def demos(text):
    return re.sub(r'(<pre class="code"[^>]*\bdata-demo\b[^>]*>)(.*?)(</pre>)', lambda m: m.group(1) + highlight(m.group(2)) + m.group(3), text, flags=re.S)


def stage_slides(proj, name, st):
    text = (ROOT / name / "slides" / ("stage%d.html" % st["id"])).read_text(encoding="utf-8")
    made = {"cover": cover(proj, st), "review": review(proj, st),
            "spec": "".join(spec_page(proj, st, fn) for fn in st["functions"]),
            "folder": folder_page(proj, name, st), "run": run_page(proj, st, starter_failures(proj, name, st)),
            "play": play_page(proj, st), "tell": tell_page(proj, st)}
    for key, page in made.items():
        assert text.count("<!-- @%s -->" % key) == 1, "%s stage %d: slides need <!-- @%s --> once" % (name, st["id"], key)
        text = text.replace("<!-- @%s -->" % key, page.strip())
    count = 0

    def number(match):
        nonlocal count
        count += 1
        return '<section id="page-%d" class="slide%s' % (count, " active visible" if count == 1 else "")
    return re.sub(r'<section class="slide', number, demos(text).rstrip() + "\n" + thanks(proj, name, st))


def render_deck(proj, name, st):
    css = "\n".join([FONTS, basics_read("vendor/viewport.css"), basics_read("template/theme.css"),
                     (ROOT / "template" / "project.css").read_text(encoding="utf-8")])
    script = basics_read("template/deck.js").replace("{{ide}}", json.dumps(BASICS_SITE["ide"], ensure_ascii=False)).replace("{{language}}", LANGUAGE)
    title = "第 %d 关：%s" % (st["id"], st["title"])
    page = basics_read("template/page.html")
    fields = dict(title=esc(title), file=sf.names(LANGUAGE, proj, st["id"])[0], css=css, site=esc("%s · %s" % (proj.PROJECT["title"], SITE["title"])),
                  slides=stage_slides(proj, name, st).rstrip(), script=script.rstrip())
    for key, value in fields.items():
        page = page.replace("{{" + key + "}}", value)
    return page.replace("<!-- Generated by tools/build.py. Edit lessons/ and template/, not this file. -->",
                        "<!-- Generated by project/tools/build.py. Edit project/, not this file. -->")


# ---------------------------------------------------------------- map and index pages

def given_and_back(fn):
    lines = sf.spec(fn, LANGUAGE)[1]
    pick = lambda head: next((l.split("：", 1)[1] for l in lines if l.startswith(head)), "")
    return pick("给它"), pick("还给你")


def render_map(proj, name):
    stages = []
    for st in proj.STAGES:
        n = st["id"]
        fns = "".join("<code>%s</code>" % esc(fn["name"]) for fn in st["functions"])
        needs = "".join('<a href="%s%s/index.html">%s</a>' % (esc(SITE["basics"]), esc(f), esc(f)) for f, _ in sf.needs(st, LANGUAGE))
        stages.append('''<li><div class="n">%d</div><div><h3>%s</h3><p>%s</p><p class="fns">要写：%s</p><p class="needs">先学完：%s</p></div>
<nav aria-label="第 %d 关"><a class="go" href="stage%d/index.html">放映课件</a><a href="download/%s-stage%d.zip" download>下载 zip</a><a href="download/stage%d/guide.md">引导文档</a></nav></li>'''
                      % (n, esc(st["title"]), esc(st["goal"]), fns, needs, n, n, name, n, n))
    table = "".join("<tr><td><code>%s</code></td><td>%d</td><td>%s</td><td>%s</td></tr>" % ((esc(fn["name"]), st["id"]) + tuple(code_text(x) for x in given_and_back(fn)))
                    for st in proj.STAGES for fn in st["functions"])
    me = sf.names(LANGUAGE, proj, 1)
    body = '''
<header class="hero"><div class="in">
  <nav class="crumbs"><a href="../index.html">← 项目课</a></nav>
  <h1>%s</h1>
  <p class="lead">%s</p>
  <p class="lead small">从基础课件 <a href="%s%s/index.html">%s</a> 学完就能开始。代码在自己的电脑上写和运行，编辑器不限（PyCharm、VS Code 都行）。</p>
  <div class="actions"><a class="start" href="stage1/index.html">▶ 从第 1 关开始</a><a class="second" href="download/%s-all.zip" download>⬇ 下载全部 %d 关（zip）</a></div>
</div></header>
<main>
  <section><h2>项目地图</h2><ol class="route">%s</ol></section>
  <section><h2>函数一览</h2><p>名字必须照写：老师的测试按这些名字检查。</p>
    <table><thead><tr><th>函数</th><th>关</th><th>给它</th><th>还给你</th></tr></thead><tbody>%s</tbody></table></section>
  <section><h2>给老师：准备 U 盘</h2><ol class="plain">
    <li>下载全部关卡的 zip，在电脑上解压。</li>
    <li>把解压出来的 <code>stage1</code> 到 <code>stage%d</code> 文件夹拷进 U 盘。拷文件夹本身，不要只拷 zip：在 zip 里直接运行会找不到同一个文件夹里的文件。</li>
    <li>参考答案不在下载包里，在仓库的 <code>project/%s/answers/</code>，不要拷给学生。</li>
    <li>学生用编辑器打开某一关的文件夹，改 <code>%s</code>，运行 <code>test_stageN</code> 检查，全过以后运行 <code>%s</code> 玩。</li>
  </ol></section>
</main>
''' % (esc(proj.PROJECT["title"]), esc(proj.PROJECT["lead"]), esc(SITE["basics"]), esc(proj.PROJECT["start"][LANGUAGE]), esc(proj.PROJECT["start"][LANGUAGE]),
       name, len(proj.STAGES), "\n".join(stages), table, len(proj.STAGES), name, esc(me[0]), esc(me[2]))
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
    """A zip of {folder name: {file: text}}, the same bytes every time for the same files."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, files in folders.items():
            for file in sorted(files):
                info = zipfile.ZipInfo("%s/%s" % (folder, file), ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, files[file].encode("utf-8"))
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
            for file, text in stage.items():
                files[DIST / name / "download" / ("stage%d" % n) / file] = text.encode("utf-8")
            files[DIST / name / "download" / ("%s-stage%d.zip" % (name, n))] = zip_bytes({"stage%d" % n: stage})
            files[ROOT / name / "answers" / ("stage%d" % n) / sf.names(LANGUAGE, proj, n)[0]] = sf.answer_file(proj, st, LANGUAGE).encode("utf-8")
        files[DIST / name / "download" / ("%s-all.zip" % name)] = zip_bytes(folders)
        files[DIST / name / "index.html"] = render_map(proj, name).encode("utf-8")
    files[DIST / "index.html"] = render_index(projects).encode("utf-8")
    return files, projects


def main():
    # Stage folders first: the slides count how many tests each untouched starter fails.
    files, projects = outputs()
    for name, _ in projects:
        shutil.rmtree(DIST / name, ignore_errors=True)
        shutil.rmtree(ROOT / name / "answers", ignore_errors=True)
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    decks = 0
    for name, proj in projects:
        for st in proj.STAGES:
            path = DIST / name / ("stage%d" % st["id"]) / "index.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_deck(proj, name, st), encoding="utf-8")
            decks += 1
    print("Built %d project(s), %d stage decks and their folders into dist/" % (len(projects), decks))


if __name__ == "__main__":
    main()
