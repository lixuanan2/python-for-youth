#!/usr/bin/env python3
"""Build every lesson into dist/: one offline HTML deck, its starter files and an index.

Usage: python3 tools/build.py [--pdf] [--chrome PATH]
Only the Python standard library is needed. --pdf also prints each deck with Chrome.
"""
import argparse
import base64
import html
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
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


def thanks_slide(lesson):
    """Every deck ends the same way: its program finishes, with this lesson's own details."""
    items = course()
    following = items[items.index(lesson) + 1] if items.index(lesson) + 1 < len(items) else None
    if following is None:
        onward = '<p class="abs say r d3" style="left:96px;top:872px">这门课的路线走完了，了不起！</p>'
    elif 'id' in following:
        onward = f'<a class="go-next r d3" href="../{following["id"]}/index.html">下一课：{html.escape(following["title"])}</a>'
    else:
        onward = f'<p class="abs say r d3" style="left:96px;top:872px">下一课“{html.escape(following["title"])}”还在准备中。</p>'
    command = site()['thanks']['command'].format(file=lesson['file'], stem=lesson['file'].rsplit('.', 1)[0])
    learned = '  '.join(html.escape(item) for item in lesson['learned'])
    return f'''
<!-- generated for every lesson by tools/build.py -->
<section class="slide dark thanks" aria-label="谢谢">
  <h2 class="abs r" style="left:96px;top:70px;font:800 150px/1.2 var(--text)">谢谢！</h2>
  <div class="term r d1"><span class="dim">$ {html.escape(command)}</span>
<span>谢谢你认真学完这一课</span>
<span>今天解锁：<b>{learned}</b></span>
<span class="dim">Process finished with exit code 0</span><i></i></div>
  <p class="abs say r d2" style="left:96px;top:740px">exit code 0 表示程序顺利跑完了，今天的你也是。</p>
  {onward}
</section>
'''


def attach_code(slides, lesson):
    """Fill IDE data from files: data-code-file for buttons, data-lines for excerpts of a longer program."""
    def source(file):
        text = read(f'lessons/{lesson["id"]}/{file}')
        return html.escape(text, quote=True).replace('\n', '&#10;')

    slides = re.sub(r'data-code-file="([^"]+)"', lambda m: f'data-code="{source(m.group(1))}"', slides)
    return re.sub(r'data-file="([^"]+)"( data-lines="[^"]+")', lambda m: f'data-file="{m.group(1)}"{m.group(2)} data-full="{source(m.group(1))}"', slides)


def render(lesson):
    css = '\n'.join([font_face(w) for w in (400, 700, 800)] + [read('vendor/viewport.css'), read('template/theme.css')])
    page = read('template/page.html')
    fields = dict(title=html.escape(lesson['title']), file=lesson['file'], css=css,
                  site=html.escape(site()['title']),
                  slides=attach_code(number_slides(read(f'lessons/{lesson["id"]}/slides.html').rstrip() + '\n' + thanks_slide(lesson)), lesson).rstrip(),
                  script=read('template/deck.js').replace('{{ide}}', json.dumps(site()['ide'], ensure_ascii=False)).rstrip())
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def stop(number, item):
    if 'id' not in item:
        return f'<li class="stop" data-n="{number}">{html.escape(item["title"])}</li>'
    target = item['id']
    return f'''<li class="ready"><div><h4>{html.escape(item["title"])}</h4><p>{item.get("note") or f'第 {number} 课'}，{read(f"lessons/{target}/slides.html").count("<section") + 1} 页，含小测、动手题和小项目</p></div>
<nav aria-label="{html.escape(item["title"])}"><a href="{target}/index.html">放映课件</a><a href="{target}/slides.pdf" target="_blank" rel="noopener noreferrer">PDF</a><a href="{target}/starter/">起始程序</a></nav></li>'''


def render_index(items):
    stages = {}
    counted = [item for item in items if not item.get('sample')]
    number = 0
    for item in items:
        number += not item.get('sample')
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


def outputs():
    """Everything in dist/ that comes from a template, as {path: text}."""
    files = {DIST / 'index.html': render_index(course())}
    for lesson in lessons():
        files[DIST / lesson['id'] / 'index.html'] = render(lesson)
    return files


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
    for path, text in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')
    for lesson in lessons():
        shutil.copytree(ROOT / 'lessons' / lesson['id'] / 'starter', DIST / lesson['id'] / 'starter', dirs_exist_ok=True)
    print(f'Built {len(lessons())} lesson(s) into dist/')
    if args.pdf:
        chrome = args.chrome or next((c for c in CHROME if Path(c).is_file()), None)
        if not chrome:
            parser.error('Chrome not found; pass --chrome')
        for lesson in lessons():
            print_pdf(lesson, chrome)


if __name__ == '__main__':
    main()
