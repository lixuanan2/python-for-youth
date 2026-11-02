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


def course():
    return json.loads((ROOT / 'course.json').read_text(encoding='utf-8'))


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


def render(lesson):
    css = '\n'.join([font_face(w) for w in (400, 700, 800)] + [read('vendor/viewport.css'), read('template/theme.css')])
    page = read('template/page.html')
    fields = dict(title=html.escape(lesson['title']), file=lesson['file'], css=css,
                  slides=number_slides(read(f'lessons/{lesson["id"]}/slides.html')).rstrip(),
                  script=read('template/deck.js').rstrip())
    for key, value in fields.items():
        page = page.replace('{{' + key + '}}', value)
    return page


def render_index(lessons):
    rows = ''.join(f'<a href="{item["id"]}/index.html"><span>{html.escape(item["tag"])}</span>{html.escape(item["title"])}</a>' for item in lessons)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Python for Kids</title>
<style>body{{margin:0 auto;max-width:760px;padding:64px 20px;background:#faf9f5;color:#141413;font-family:"Microsoft YaHei","PingFang SC",sans-serif}}
h1{{font-size:40px;margin:0 0 32px}}a{{display:flex;gap:24px;padding:20px 0;border-top:3px solid #141413;color:inherit;text-decoration:none;font-size:26px;font-weight:700}}
a:hover{{color:#c6613f}}span{{color:#c6613f;font-family:Consolas,Menlo,monospace;font-weight:400}}</style></head>
<body><h1># Python 课程</h1>{rows}</body></html>
'''


def outputs():
    """Everything in dist/ that comes from a template, as {path: text}."""
    lessons = course()
    files = {DIST / 'index.html': render_index(lessons)}
    for lesson in lessons:
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
    for lesson in course():
        shutil.copytree(ROOT / 'lessons' / lesson['id'] / 'starter', DIST / lesson['id'] / 'starter', dirs_exist_ok=True)
    print(f'Built {len(course())} lesson(s) into dist/')
    if args.pdf:
        chrome = args.chrome or next((c for c in CHROME if Path(c).is_file()), None)
        if not chrome:
            parser.error('Chrome not found; pass --chrome')
        for lesson in course():
            print_pdf(lesson, chrome)


if __name__ == '__main__':
    main()
