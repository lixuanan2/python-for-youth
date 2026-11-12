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
BRIEF_ROLES = ('学生小改写', '独立迁移', '创作项目')
START = {'学生小改写': '在下面这段程序上改', '独立迁移': '从这里开始写', '创作项目': '从这里开始造'}
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
    if brief.get('sample', task['role'] != '创作项目'):
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


def render(lesson):
    css = '\n'.join([font_face(w) for w in (400, 700, 800)] + [read('vendor/viewport.css'), read('template/theme.css')])
    page = read('template/page.html')
    fields = dict(title=html.escape(lesson['title']), lesson=css_string(lesson_label(lesson)), css=css,
                  site=html.escape(site()['title']),
                  slides=algo.embed(attach_code(number_slides(read(f'lessons/{lesson["id"]}/slides.html').rstrip() + '\n' + thanks_slide(lesson)), lesson), site()['language']).rstrip(),
                  script=read('template/deck.js').replace('{{ide}}', json.dumps(site()['ide'], ensure_ascii=False)).replace('{{language}}', site()['language']).rstrip())
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def stop(number, item):
    if 'id' not in item:
        return f'<li class="stop" data-n="{number}">{html.escape(item["title"])}</li>'
    target = item['id']
    return f'''<li class="ready"><div><h4>{html.escape(item["title"])}</h4><p>{item.get("note") or f'第 {number} 课'}，{read(f"lessons/{target}/slides.html").count("<section") + 1} 页，含小测、动手题和小项目</p></div>
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
