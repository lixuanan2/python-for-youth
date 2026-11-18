#!/usr/bin/env python3
"""Build every lesson into dist/: one offline HTML deck, its starter files and an index.

Usage: python3 tools/build.py [--pdf] [--chrome PATH]
Only the Python standard library is needed. --pdf also prints with Chrome every deck whose PDF is out of date.
"""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote

import algo

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
# Which deck each slides.pdf was printed from, so tools/check.py can tell when a PDF falls behind its page.
PDF_RECORD = ROOT / 'pdf.json'
CHROME = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/usr/bin/google-chrome',
]


def site():
    return json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))


def course():
    return json.loads((ROOT / 'course.json').read_text(encoding='utf-8'))


def lessons():
    """Entries with an id are built; the rest are planned stops on the route."""
    return [item for item in course() if 'id' in item]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def font_face(weight):
    data = (ROOT / f'vendor/fonts/jetbrains-mono-latin-{weight}-normal.woff2').read_bytes()
    encoded = base64.b64encode(data).decode()
    return f'@font-face{{font-family:"JetBrains Mono";font-weight:{weight};font-style:normal;src:url(data:font/woff2;base64,{encoded}) format("woff2")}}'


def number_slides(slides):
    """Give sections page ids in order; the first one is shown before scripts run."""
    count = 0

    def mark(match):
        nonlocal count
        count += 1
        extra = ' active visible' if count == 1 else ''
        return f'<section id="page-{count}" class="slide{extra}'

    return re.sub(r'<section class="slide', mark, slides)


HOME_LINK = '<a class="go-next r d3" href="../index.html">回到课程首页</a>'


def thanks_link(link):
    icon = read(f'template/icons/{link["icon"]}.svg').strip()
    return (f'<a class="gh-link" href="{html.escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{icon}{html.escape(link["label"])}</a>')


def thanks_slide(lesson):
    """Every deck ends with the same short thank-you, the course links and the way onward."""
    items = course()
    following = items[items.index(lesson) + 1] if items.index(lesson) + 1 < len(items) else None
    if following is None:
        onward = HOME_LINK + '<p class="abs say r d3 next-note">这门课的路线走完了，了不起！</p>'
    elif 'id' in following:
        onward = f'<a class="go-next r d3" href="../{following["id"]}/index.html">下一课：{html.escape(following["title"])}</a>'
    else:
        onward = HOME_LINK + f'<p class="abs say r d3 next-note">下一课“{html.escape(following["title"])}”还在准备中</p>'
    thanks = site()['thanks']
    links = ''.join(thanks_link(link) for link in thanks['links'])
    return f'''
<!-- generated for every lesson by tools/build.py -->
<section class="slide dark thanks" aria-label="谢谢">
  <h2 class="abs r" style="left:96px;top:130px;font:800 240px/1.2 var(--text)">谢谢！</h2>
  <p class="abs say r d1" style="left:96px;top:470px;font-size:52px">{html.escape(thanks['message'])}</p>
  <div class="links r d2">{links}</div>
  {onward}
</section>
'''


# Practice the students write themselves: their starter opens with the task told again, so the IDE alone is enough.
BRIEF_ROLES = ('学生小改写', '独立迁移')
START = {'学生小改写': '在下面这段程序上改', '独立迁移': '从这里开始写'}
BRIEF_LINES = 12  # about one screen of the IDE above the code
WIDTH = 64  # columns, a Chinese character counting two


def columns(text):
    return sum(2 if ord(ch) > 0x2e7f else 1 for ch in text)


def wrap(text, first=''):
    """Lines of at most WIDTH columns, broken after punctuation where it can be."""
    out, line = [], first
    for piece in re.findall(r'[^，。；：、]*[，。；：、]?', text):
        if not piece:
            continue
        if line.strip() and columns(line + piece) > WIDTH:
            out.append(line)
            line = '  '
        line += piece
    return out + [line]


def shown_lines(text):
    return text.split('\n')[:-1] if text.endswith('\n') else text.split('\n')


def sample_lines(task, brief):
    """The tested sample, told the way a page tells it."""
    given, want = shown_lines(brief.get('input', task['sample_input'])), shown_lines(brief.get('output', task['sample_output']))
    lines = []
    joined = lambda items: ' / '.join(items) if any(re.search('[、,，]', i) for i in items) else '、'.join(items)
    if given and given != ['']:
        lines.append('例如输入：' + given[0] if len(given) == 1 else f'例如输入（每个一行）：{joined(given)}')
    head = '应该输出' if lines else '运行后应该输出'
    if len(want) == 1:
        lines.append(f'{head}：{want[0]}')
    elif len(want) <= 8 and all(columns(w) <= 12 for w in want) and columns(joined(want)) <= 44:
        lines.append(f'{head}（每个一行）：{joined(want)}')
    elif len(want) <= 3:
        lines += [f'{head}：'] + ['  ' + w for w in want]
    else:
        # Every line, so the sample never reads like text is missing: side by side when that saves room.
        rows = ['  ']
        for k, w in enumerate(want):
            piece = w if k == 0 else ' / ' + w
            if rows[-1].strip() and columns(rows[-1] + piece) > WIDTH:
                rows.append('  ')
                piece = w
            rows[-1] += piece
        if len(rows) < len(want):
            lines += [f'{head}（一共 {len(want)} 行，这里用 / 隔开）：'] + rows
        else:
            lines += [f'{head}（一共 {len(want)} 行）：'] + ['  ' + w for w in want]
    return lines


def brief_header(task, comment):
    """What to do, the input and output, a sample and a hint, as comments: one source, tasks.json "brief"."""
    brief = task.get('brief')
    if not brief or task['role'] not in BRIEF_ROLES:
        return ''
    lines = [f'【{brief["title"]}】']
    for sentence in brief['goal']:
        lines += wrap(sentence)
    if brief.get('sample', True):
        lines += sample_lines(task, brief)
    for extra in ([f'提示：{brief["hint"]}'] if brief.get('hint') else []) + brief.get('more', []):
        lines += wrap(extra)
    lines.append('↓ ' + START[task['role']])
    return ''.join(f'{comment} {line}'.rstrip() + '\n' for line in lines)


def starter_text(lesson, name):
    """A starter file as students get it, in IDE links, on the starter page and as a download."""
    folder = ROOT / 'lessons' / lesson['id']
    body = (folder / name).read_text(encoding='utf-8')
    task = next((t for t in json.loads((folder / 'tasks.json').read_text(encoding='utf-8')) if t['starter'] == name and t.get('brief')), None)
    header = brief_header(task, '#' if site()['language'] == 'python' else '//') if task else ''
    return header + ('\n' + body.lstrip('\n') if header and body.strip() else body)


def attach_code(slides, lesson):
    """Fill IDE data from files: data-code-file for buttons, data-lines for excerpts of a longer program."""
    def source(file):
        text = starter_text(lesson, file) if file.startswith('starter/') else read(f'lessons/{lesson["id"]}/{file}')
        return html.escape(text, quote=True).replace('\n', '&#10;')

    slides = re.sub(r'data-code-file="([^"]+)"', lambda m: f'data-code="{source(m.group(1))}"', slides)
    # A page that shows only part of a program marks the whole, tested program in claims.json with "ide": true.
    marked = [claim for claim in json.loads(read(f'lessons/{lesson["id"]}/tests/claims.json')) if claim.get('ide')]
    pages = [claim['page'] for claim in marked]
    assert len(pages) == len(set(pages)), f'Two IDE programs for one page in {lesson["id"]}'
    for claim in marked:
        full = html.escape(claim['code'], quote=True).replace('\n', '&#10;')
        slides, found = re.subn(f'<section id="page-{claim["page"]}" ', f'<section id="page-{claim["page"]}" data-ide="{full}" ', slides)
        assert found == 1, f'No page {claim["page"]} for the IDE program in {lesson["id"]}'
    return re.sub(r'data-file="([^"]+)"( data-lines="[^"]+")', lambda m: f'data-file="{m.group(1)}"{m.group(2)} data-full="{source(m.group(1))}"', slides)


def lesson_number(item, previous):
    """第几课: the number in front of the id, so both halves of a split lesson (05a, 05b) are lesson 5; a planned lesson with no id comes next."""
    found = re.match(r'\d+', item.get('id', ''))
    return int(found.group()) if found else previous + 1


def lesson_label(lesson):
    """The left of the status bar on every page: 第 7 课 while 循环. A split lesson's title already says 上集 or 下集."""
    return f'第 {lesson_number(lesson, 0)} 课 {lesson["title"]}'


def css_string(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('<', '\\3c ') + '"'


KEYWORDS = {'python': r'\b(?:def|return|if|elif|else|for|while|in|and|or|not|is|True|False|None|import|from|as|break|continue|try|except|pass|global|lambda)\b',
            'cpp': r'(?:#include|\b(?:int|long|double|float|char|bool|void|string|auto|const|struct|return|if|else|for|while|do|break|continue|true|false|using|namespace)\b)'}
# A string may start with f (f-string): the f takes the string's colour, as on the hand-coloured pages.
TOKEN = r'(?P<s>(?:\bf)?\'[^\']*\'|(?:\bf)?"[^"]*")|(?P<m>\b\d+(?:\.\d+)?\b)|(?P<f>\b\w+(?=\())|(?P<k>%s)'


def highlight(code):
    """Program text as an editor shows it: one .ln per line, coloured with the classes the slides use."""
    token = re.compile(TOKEN % KEYWORDS[site()['language']])

    def line(text):
        out, at = [], 0
        for m in token.finditer(text):
            out.append(html.escape(text[at:m.start()], quote=False))
            out.append(f'<span class="{m.lastgroup}">{html.escape(m.group(), quote=False)}</span>')
            at = m.end()
        return '<span class="ln">' + ''.join(out) + html.escape(text[at:], quote=False) + '</span>'
    return ''.join(line(text) for text in code.split('\n'))


# === LAYOUTS: a page with a layout (class lay-walk and so on, template/layouts.css) names its cells and carries no
# coordinates. Its code boxes, and a free page's, hold plain code and are coloured here. Other pages are built as before.
# A lesson marked "structured": true in course.json has moved every page over (check.py then wants a layout on each).

def structured(lesson):
    return bool(lesson.get('structured'))


# A page moved over: it names a layout, or it is a free page (class free) that keeps its own left/top.
LAID_OUT = re.compile(r'<section class="slide[^"]* (?:lay-|free\b)')


def uses_layouts(slides):
    return bool(LAID_OUT.search(slides))


def numbers(text):
    """'2', '2,4', '3-5' or '1,3-4' as a list of numbers."""
    out = []
    for part in text.split(','):
        a, _, b = part.strip().partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return out


LN_OPEN = re.compile(r'<span class="ln([^"]*)">')


def mark_lines(inner, light, mod, where):
    """data-light="1-2:2 3:3-5": lines 1 and 2 light up on step 2, line 3 on steps 3 to 5 (classes l2, l3 ...).
    data-mod="2:原来是 >=": line 2 is a changed line, with a grey note of what it was (classes mod and orig)."""
    lines = len(LN_OPEN.findall(inner))
    extra, notes = {}, {}
    for group in (light or '').split():
        rows, _, steps = group.partition(':')
        assert steps, f'{where}: data-light needs line:step, like 1-2:2, not {group}'
        for n in numbers(rows):
            assert 1 <= n <= lines, f'{where}: data-light names line {n}, the code has {lines}'
            extra.setdefault(n, []).extend(f'l{k}' for k in numbers(steps))
    for item in (mod or '').split('|'):
        if item.strip():
            row, _, note = item.partition(':')
            n = int(row)
            assert 1 <= n <= lines and note.strip(), f'{where}: data-mod needs line:note, like 2:原来是 >=, not {item}'
            extra.setdefault(n, []).append('mod')
            notes[n] = note.strip()
    count = 0

    def opening(match):
        nonlocal count
        count += 1
        classes = match.group(1).split() + [c for c in extra.get(count, []) if c not in match.group(1).split()]
        return '<span class="' + ' '.join(['ln'] + classes) + '">'
    inner = LN_OPEN.sub(opening, inner)
    for n, note in sorted(notes.items(), reverse=True):  # the note goes at the end of its line, before the line closes
        starts = [m.start() for m in LN_OPEN.finditer(inner)] + [len(inner)]
        end = inner.rindex('</span>', starts[n - 1], starts[n])
        inner = inner[:end] + f'<span class="orig">{html.escape(note, quote=False)}</span>' + inner[end:]
    return inner


CODE_BOX = re.compile(r'<pre class="code([^"]*)"([^>]*)>(.*?)</pre>', re.S)
COLOURED = re.compile(r'<span class="[kmfs]">')


def build_code(slides, lesson):
    """Colour each code box on a page with a layout from its code: written in the page, or from data-file when the box is empty."""
    def box(match):
        classes, attrs, inner = match.groups()
        where = f'{lesson["id"]}: code box {html.unescape(attrs.strip())[:60]}'
        get = lambda name: (re.search(f' {name}="([^"]*)"', attrs) or [None, None])[1]
        if '<span class="ln' not in inner:
            code = html.unescape(inner).strip('\n')
            if not code.strip() and get('data-file'):
                code = read(f'lessons/{lesson["id"]}/{get("data-file")}').strip('\n')
                if get('data-lines'):
                    first, last = map(int, get('data-lines').split('-'))
                    code = '\n'.join(code.split('\n')[first - 1:last])
            assert code.strip(), f'{where}: an empty code box needs data-file'
            inner = highlight(code)
        elif 'pick' not in classes.split() and '<input' not in inner:
            # Two kinds keep colours written by hand: a bug hunt (.pick), whose mistakes must not be coloured as if right,
            # and a box with yellow boxes (input.slot) in its code.
            assert not COLOURED.search(inner), f'{where}: write the code without colour spans; the build colours it'
        light, mod = get('data-light'), get('data-mod')
        attrs = re.sub(r' data-(?:light|mod)="[^"]*"', '', attrs)
        inner = mark_lines(inner, html.unescape(light or ''), html.unescape(mod or ''), where)
        return f'<pre class="code{classes}"{attrs}>{inner}</pre>'
    return re.sub(r'<section class="slide.*?</section>', lambda page: CODE_BOX.sub(box, page.group()) if LAID_OUT.match(page.group()) else page.group(),
                  slides, flags=re.S)


# Where each layout puts its code box: (width, height for the box, largest font). The build picks the font so the code
# fits; a page can still set --fs or a width of its own. Keep in step with template/layouts.css.
# In walk and predict the sentences go under the code, so the height is what the column leaves after them (code_height).
CODE_ROOM = {'walk': (960, 790, 52), 'walk wide': (1060, 790, 52), 'walk narrow': (840, 790, 52),
             'predict': (1000, 740, 58), 'ask': (800, 600, 48), 'ask bug': (1040, 640, 50), 'try': (1200, 260, 44)}
# An editor may hold two versions of its code (pre.code.was, then the new one shown from data-change); the font fits both.
EDITOR = re.compile(r'<div class="editor([^"]*)"((?: [\w-]+="[^"]*")*)>(\s*<div class="tab">.*?</div>((?:\s*<pre class="code[^"]*"[^>]*>.*?</pre>)+))', re.S)


def code_room(section):
    found = re.search(r'<section class="slide([^"]*)"', section)
    names = found.group(1).split() if found else []
    layout = next((n[4:] for n in names if n.startswith('lay-')), None)
    if layout == 'walk':
        layout += next((' ' + n for n in names if n in ('wide', 'narrow')), '')
    if layout == 'ask' and 'class="code pick' in section:
        layout = 'ask bug'
    return CODE_ROOM.get(layout)


def outside(section, *cells):
    """The page without the named cells (div.right, div.answer): what is left shares the code's column."""
    for cell in cells:
        while (found := re.search(f'<div class="{cell}[" ]', section)):
            depth = 0
            for m in re.finditer(r'<div\b|</div>', section[found.start():]):
                depth += -1 if m.group().startswith('</') else 1
                if depth == 0:
                    section = section[:found.start()] + section[found.start() + m.end():]
                    break
    return section


def code_height(section, layout, width, column):
    """Walk and predict: the column holds the code, a gap, the sentence (one of .turns at a time) and, in walk, the IDE button."""
    if not layout.startswith(('walk', 'predict')):
        return column
    rest = outside(section, 'right', 'answer')
    lines = 0
    for say in re.findall(r'<p class="say[^"]*"[^>]*>(.*?)</p>', rest, re.S):
        parts = [html.unescape(re.sub(r'<[^>]+>', '', part)) for part in re.split(r'<br\s*/?>', say)]
        lines = max(lines, sum(-(-sum(10 if ord(ch) > 0x2e7f else 6 for ch in part) * 4 // width) or 1 for part in parts))
    gap = 40 if layout.startswith('walk') else 50
    button = 115 if layout.startswith('walk') and '<a class="ide' in rest else 0
    return column - (gap + lines * 64 if lines else 0) - button


def fit_code(slides, lesson):
    """Give each code box a font size that fits its layout, from its line count and longest line."""
    def section(page):
        room = code_room(page.group())
        if not room:
            return page.group()
        layout = next(name for name, value in CODE_ROOM.items() if value is room)
        room = (room[0], code_height(page.group(), layout, room[0], room[1]), room[2])

        def editor(match):
            classes, attrs, body, inner = match.groups()
            if '--fs' in attrs:
                return match.group()
            width, height, top = room
            own = re.search(r'width:\s*(\d+)px', attrs)
            width = int(own.group(1)) if own else width
            versions = [[html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<span class="orig">.*?</span>', '', l)))
                         for l in re.findall(r'<span class="ln[^"]*">(.*?)</span>(?=<span class="ln|$)', code, re.S)] or ['']
                        for code in re.findall(r'<pre[^>]*>(.*?)</pre>', inner, re.S)]
            # The grey "原来是 ..." note sits at the end of its line in a smaller font; it does not set the size.
            widest = max(sum(10 if ord(ch) > 0x2e7f else 6 for ch in l) for lines in versions for l in lines) or 1
            size = min(top, (width - GUTTER) * 10 // widest, (height - 130) * 100 // (155 * max(map(len, versions))))
            assert size >= 30, f'{lesson["id"]}: a code box needs {size}px to fit its layout; cut lines or give it room'
            style = re.search(r' style="([^"]*)"', attrs)
            attrs = re.sub(r' style="[^"]*"', '', attrs) + f' style="{(style.group(1).rstrip(";") + ";") if style else ""}--fs:{size}px"'
            return f'<div class="editor{classes}"{attrs}>{body}'
        return EDITOR.sub(editor, page.group())
    return re.sub(r'<section class="slide.*?</section>', section, slides, flags=re.S)


# <!-- @answer 04 | 一两句讲解 --> or <!-- @answer 02 lines 5-14 | … --> in slides.html: the reference answer of a challenge
# (tasks.json role 独立迁移), straight from its tested solution. The page opens covered; the teacher turns the next step to show it.
ANSWER = re.compile(r'<!-- @answer (\S+)(?: lines (\d+)-(\d+))? \| (.+?) -->')
GUTTER = 156  # an editor's line numbers and padding, in px


def answer_page(match, lesson):
    tasks = {t['id']: t for t in json.loads(read(f'lessons/{lesson["id"]}/tasks.json'))}
    task_id, first, last, say = match.groups()
    task = tasks.get(task_id)
    assert task and task['role'] == '独立迁移', f'{lesson["id"]}: @answer {task_id} is not a challenge (独立迁移) in tasks.json'
    code = read(f'lessons/{lesson["id"]}/{task["solution"]}').strip()
    lines = code.split('\n')
    shown = lines[int(first) - 1:int(last)] if first else lines
    # Width in tenths of the font size: a code character is 6, a Chinese one 10. Whole numbers, so every Python agrees.
    widest = max(sum(10 if ord(ch) > 0x2e7f else 6 for ch in l) for l in shown)
    font = lambda width, height: min(44, (width - GUTTER) * 10 // widest, height * 100 // (155 * len(shown)))
    # The explanation sits in a column on the right; a program with long lines takes the full width and the
    # explanation goes under it in one line.
    if font(1180, 650) >= 34:
        size, width = font(1180, 650), 1180
        aside = f'  <p class="abs say step s2" style="left:1340px;top:220px;width:484px">{say}</p>\n' \
                '  <a class="ide step s2" style="left:1340px;top:860px">▶ 在 IDE 打开</a>\n'
    else:
        size, width = font(1728, 540), 1728
        assert len(re.sub(r'<[^>]+>', '', say)) <= 30, f'{lesson["id"]}: under a wide answer the explanation has one line; keep it to 30 characters'
        aside = f'  <p class="abs say step s2" style="left:96px;top:890px;width:1300px">{say}</p>\n' \
                '  <a class="ide step s2" style="left:1480px;top:880px">▶ 在 IDE 打开</a>\n'
    assert size >= 26, f'{lesson["id"]}: the answer to {task_id} needs a font of {size}px; show its key lines with "lines A-B"'
    title = html.escape(task['brief']['title'])
    tab = html.escape(re.sub(r'^\d+[a-z]?_', '', task['solution'].split('/')[-1]))
    picked = f' data-lines="{first}-{last}"' if first else ''
    return (f'<section class="slide dark" aria-label="参考答案：{title}" data-answer="{task_id}" data-steps="2" data-at="2">\n'
            f'  <h2 class="t">参考答案：{title}</h2>\n'
            '  <div class="abs only1" style="left:96px;top:330px;width:1728px;text-align:center">'
            '<p class="say" style="font-size:64px;font-weight:800">先自己做完，再翻开对一对</p>'
            '<p class="say" style="color:var(--ghost);margin-top:24px">讲的时候按 → 翻开</p></div>\n'
            f'  <div class="editor step s2" style="left:96px;top:200px;width:{width}px;--fs:{size}px"><div class="tab">{tab}</div>\n'
            f'<pre class="code" data-file="{task["solution"]}"{picked}>{highlight(chr(10).join(shown))}</pre></div>\n'
            + aside +
            '  <div class="foot"></div>\n'
            '</section>')


def answer_pages(slides, lesson):
    return ANSWER.sub(lambda m: answer_page(m, lesson), slides)


def render(lesson):
    slides = read(f'lessons/{lesson["id"]}/slides.html').rstrip()
    sheets = [read('vendor/viewport.css'), read('template/theme.css')] + ([read('template/layouts.css')] if uses_layouts(slides) else [])
    css = '\n'.join([font_face(w) for w in (400, 700, 800)] + sheets)
    page = read('template/page.html')
    if uses_layouts(slides):
        slides = fit_code(build_code(slides, lesson), lesson)
    fields = dict(title=html.escape(lesson['title']), lesson=css_string(lesson_label(lesson)), css=css,
                  site=html.escape(site()['title']),
                  slides=algo.embed(attach_code(number_slides(answer_pages(slides, lesson) + '\n' + thanks_slide(lesson)), lesson), site()['language']).rstrip(),
                  script=read('template/deck.js').replace('{{ide}}', json.dumps(site()['ide'], ensure_ascii=False)).replace('{{language}}', site()['language']).rstrip())
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def stop(number, item):
    if 'id' not in item:
        return f'<li class="stop" data-n="{number}">{html.escape(item["title"])}</li>'
    target = item['id']
    return f'''<li class="ready"><div><h4>{html.escape(item["title"])}</h4><p>{item.get("note") or f'第 {number} 课'}，{read(f"lessons/{target}/slides.html").count("<section") + 1} 页，含小测、动手题和挑战</p></div>
<nav aria-label="{html.escape(item["title"])}"><a href="{target}/index.html">放映课件</a><a href="{target}/slides.pdf" target="_blank" rel="noopener noreferrer">PDF</a><a href="{target}/starter/index.html">起始程序</a></nav></li>'''


def render_index(items):
    stages = {}
    counted = [item for item in items if not item.get('sample')]
    number = 0
    for item in items:
        number = number if item.get('sample') else lesson_number(item, number)
        stages.setdefault(item['stage'], []).append(stop(number, item))
    route = '\n'.join(f'  <section class="stage"><h3>{html.escape(name)}</h3><ol class="stops">{"".join(rows)}</ol></section>' for name, rows in stages.items())
    info, hero = site(), site()['hero']
    code = '\n'.join(f'<span class="g">{n}</span>{line}' for n, line in enumerate(hero['lines'], 1))
    page = read('template/index.html')
    fields = dict(fonts='\n'.join(font_face(w) for w in (400, 700, 800)), first=next(i['id'] for i in items if 'id' in i),
                  total=str(len(counted)), ready=str(sum('id' in i for i in counted)), route=route, site=html.escape(info['title']),
                  heading='<br>'.join(html.escape(part) for part in info['title'].split(' ', 1)), lead=html.escape(info['lead']), start=html.escape(info['start']),
                  hero_file=hero['file'], hero_code=code, hero_prompt=html.escape(hero['prompt']), hero_sample=html.escape(hero['sample']),
                  hero_reply=html.escape(hero['reply']), footer=html.escape(info['footer']))
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def ide_url(code):
    """The same link deck.js makes, with the default settings, so it works without scripts."""
    ide = site()['ide']
    query = {**ide['fixed'], **{s['param']: s['options'][0][0] for s in ide['settings']}, ide['codeParam']: code}
    return ide['base'] + '?' + '&'.join(k + '=' + quote(str(v), safe="-_.!~*'()") for k, v in query.items())


def starters(lesson):
    """Starter files in the order the slides use them; files no task names go last."""
    folder = ROOT / 'lessons' / lesson['id']
    tasks = sorted(json.loads((folder / 'tasks.json').read_text(encoding='utf-8')), key=lambda t: t['page'])
    files = sorted(folder.glob('starter/*'))
    assert not any(f.name == 'index.html' for f in files), f'starter/index.html is made by the build: {lesson["id"]}'
    order = {}
    for task in tasks:
        order.setdefault(task['starter'], task)
    named = [folder / name for name in order]
    return [(f, order.get(f.relative_to(folder).as_posix())) for f in named + [f for f in files if f not in named] if f.is_file()]


def render_starter(lesson):
    """dist/<lesson>/starter/index.html: GitHub Pages lists no folders, so every lesson gets a page of its files."""
    ide = site()['ide']['name']
    rows = []
    for file, task in starters(lesson):
        code = starter_text(lesson, file.relative_to(ROOT / 'lessons' / lesson['id']).as_posix())
        name = html.escape(file.name)
        about = ''
        actions = [f'<a href="{name}" download="{name}">下载</a>', f'<a href="{html.escape(ide_url(code), quote=True)}" target="_blank" rel="noopener noreferrer">在 {html.escape(ide)} 打开</a>']
        if task:
            about = f'<p>课件第 {task["page"]} 页：{html.escape(task["description"])}</p>'
            actions.append(f'<a href="../index.html#page-{task["page"]}">看第 {task["page"]} 页</a>')
        rows.append(f'''    <li class="file"><div><h2><a href="{name}" download="{name}">{name}</a></h2>{about}</div>
      <nav aria-label="{name}">{"".join(actions)}</nav>
      <details><summary>看代码</summary><pre>{html.escape(code.rstrip())}</pre></details></li>''')
    page = read('template/starter.html')
    fields = dict(fonts='\n'.join(font_face(w) for w in (400, 700, 800)), title=html.escape(lesson['title']), count=str(len(rows)),
                  ide=html.escape(ide), files='\n'.join(rows), footer=html.escape(site()['footer']))
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def file_encoding(path):
    """Downloaded starter files use site.json "starter_encoding": "utf-8" (default), "utf-8-sig" (UTF-8 with a BOM,
    which Windows editors such as Dev-C++ 6 read as UTF-8 for sure) or "gbk" (for an editor that only reads the
    Chinese Windows code page). Everything else is UTF-8; IDE links carry text, so no encoding reaches the IDE."""
    starter = path.parent.name == 'starter' and path.name != 'index.html'
    return site().get('starter_encoding', 'utf-8') if starter else 'utf-8'


def outputs():
    """Everything in dist/ that comes from a template, as {path: text}."""
    files = {DIST / 'index.html': render_index(course())}
    for lesson in lessons():
        files[DIST / lesson['id'] / 'index.html'] = render(lesson)
        files[DIST / lesson['id'] / 'starter' / 'index.html'] = render_starter(lesson)
        for file, _ in starters(lesson):
            name = file.relative_to(ROOT / 'lessons' / lesson['id']).as_posix()
            files[DIST / lesson['id'] / name] = starter_text(lesson, name)
    return files


def stale_starters(lesson):
    """Files in dist/<lesson>/starter/ the lesson no longer has."""
    keep = {'index.html'} | {file.name for file, _ in starters(lesson)} | {f.name for f in (ROOT / 'lessons' / lesson['id'] / 'starter').glob('*')}
    folder = DIST / lesson['id'] / 'starter'
    return sorted(f for f in folder.glob('*') if f.is_file() and f.name not in keep) if folder.is_dir() else []


def digest(data):
    return hashlib.sha256(data.encode('utf-8') if isinstance(data, str) else data).hexdigest()


def pdf_stamp(lesson):
    """The deck a PDF should match and the PDF that is there now; a missing PDF has no hash."""
    pdf = DIST / lesson['id'] / 'slides.pdf'
    return {'deck': digest(render(lesson)), 'pdf': digest(pdf.read_bytes()) if pdf.is_file() else None}


def pdf_record():
    return json.loads(PDF_RECORD.read_text(encoding='utf-8')) if PDF_RECORD.is_file() else {}


def stale_pdfs():
    """Lessons whose PDF was not printed from the deck as it is now, or was changed by hand since."""
    record = pdf_record()
    return [lesson for lesson in lessons() if record.get(lesson['id']) != pdf_stamp(lesson)]


def print_pdf(lesson, chrome):
    target = DIST / lesson['id']
    subprocess.run([chrome, '--headless=new', '--no-pdf-header-footer', '--virtual-time-budget=4000',
                    f'--print-to-pdf={target / "slides.pdf"}', (target / 'index.html').as_uri()],
                   check=True, capture_output=True, timeout=120)
    print(f'Printed dist/{lesson["id"]}/slides.pdf')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', action='store_true')
    parser.add_argument('--chrome', help='Path to Chrome, if not in a usual place')
    args = parser.parse_args()
    for lesson in lessons():
        shutil.copytree(ROOT / 'lessons' / lesson['id'] / 'starter', DIST / lesson['id'] / 'starter', dirs_exist_ok=True)
        for old in stale_starters(lesson):  # a starter taken out of the lesson goes from dist/ too
            old.unlink()
    for path, text in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=file_encoding(path), newline='\n')
    print(f'Built {len(lessons())} lesson(s) into dist/')
    if args.pdf:
        chrome = args.chrome or next((c for c in CHROME if Path(c).is_file()), None)
        if not chrome:
            parser.error('Chrome not found; pass --chrome')
        record = pdf_record()
        for lesson in stale_pdfs():
            print_pdf(lesson, chrome)
            record[lesson['id']] = pdf_stamp(lesson)
        record = {lesson['id']: record[lesson['id']] for lesson in lessons() if lesson['id'] in record}
        PDF_RECORD.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Every PDF matches its deck')
    elif stale := stale_pdfs():
        print(f'{len(stale)} PDF(s) are older than their deck: {", ".join(l["id"] for l in stale)}')
        print('Run python3 tools/build.py --pdf before committing; tools/check.py stops on an old PDF.')


if __name__ == '__main__':
    main()
