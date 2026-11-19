"""README.md and the site's home page (home/index.html) from one source, home/content.json, so the two never drift apart.

    python3 tools/promo.py           write both (build.py does this too)
    python3 tools/promo.py --check   stop if either differs from what content.json makes (check.py does this)

Run in basics/. A repository without home/content.json is skipped. The page around the content (styles, the hero's live
editor, the script) is home/page.html; it has {{name}} slots for what content.json gives.

Text in content.json is written once for both: **bold**, `code`, [text](link), {slot:7} (a yellow box on the page, `7` in
the README), {kbd:F} (a key) and {lessons} (how many lessons basics/course.json has made). A link to a file in the
repository (CONTRIBUTING.md, basics/README.md) stays relative in the README and points to GitHub on the page; a link
starting with site: (site:basics/) is a page of the website, relative on the page and full in the README.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT, PAGE = ROOT / 'home' / 'content.json', ROOT / 'home' / 'page.html'
README, HOME = ROOT / 'README.md', ROOT / 'home' / 'index.html'
INLINE = re.compile(r'\*\*(?P<b>.+?)\*\*|`(?P<code>[^`]+)`|\[(?P<text>[^\]]+)\]\((?P<link>[^)]+)\)|\{slot:(?P<slot>[^}]+)\}|\{kbd:(?P<kbd>[^}]+)\}')


def link(target, c, page):
    """Where a link goes: in the README or on the page."""
    if target.startswith('site:'):
        return (target[5:] or './') if page else c['site'] + target[5:]
    if re.match(r'https?://', target):
        return target
    kind = 'tree' if target.endswith('/') or '.' not in target.rsplit('/', 1)[-1] else 'blob'
    return f'https://github.com/{c["repo"]}/{kind}/main/{target.rstrip("/")}' if page else target


def md(text, c):
    def one(m):
        if m['b']: return f'**{md(m["b"], c)}**'
        if m['code']: return f'`{m["code"]}`'
        if m['text']: return f'[{md(m["text"], c)}]({link(m["link"], c, False)})'
        if m['slot']: return f'`{m["slot"]}`'
        return f'`{m["kbd"]}`'
    return INLINE.sub(one, text)


def htm(text, c):
    out, at = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[at:m.start()], quote=False))
        if m['b']: out.append(f'<b>{htm(m["b"], c)}</b>')
        elif m['code']: out.append(f'<code>{html.escape(m["code"], quote=False)}</code>')
        elif m['text']: out.append(f'<a href="{html.escape(link(m["link"], c, True))}">{htm(m["text"], c)}</a>')
        elif m['slot']: out.append(f'<span class="slot">{html.escape(m["slot"], quote=False)}</span>')
        else: out.append(f'<kbd>{html.escape(m["kbd"], quote=False)}</kbd>')
        at = m.end()
    return ''.join(out) + html.escape(text[at:], quote=False)


def readme(c):
    s = c['sections']
    out = [f'# {c["title"]}', '', c['en'], '', md(c['lead'], c), '',
           ' '.join(f'[![{b["label"]}]({b["badge"]})]({link(b["href"], c, False)})' for b in c['buttons']), '',
           md(c['more'], c), '', f'## {s["who"]["title"]}', '']
    out += [f'- {w["h"]}：{md(w["p"], c)}' for w in s['who']['cards']]
    out += ['', f'## {s["features"]["title"]}', '']
    out += [f'- **{f["b"]}。** {md(f["p"], c)}' for f in s['features']['items']]
    out += ['', f'## {s["use"]["title"]}', '']
    out += [f'- **{u["h"]}：** {md(u["p"], c)}' for u in s['use']['cards']]
    out += ['', md(s['use']['keys'], c), '', f'## {s["modules"]["title"]}', '', '| 模块 | 内容 | 进度 |', '| --- | --- | --- |']
    for m in s['modules']['items']:
        out.append(f'| [{m["name"]}]({link(m["readme"], c, False)}) | {md(m["p"], c)} | {m["progress"]}，[在线看]({link(m["href"], c, False)}) |')
    for m in s['modules']['items']:
        if 'demo' in m:
            d = m['demo']
            out += ['', f'[![{d["alt"]}]({d["gif"]})]({link(d["video"], c, False)})', '',
                    f'{md(d["caption"], c)}点动画看[带声音的视频]({link(d["video"], c, False)})。']
    out += ['', md(s['modules']['later'], c)]
    t = s['talk']
    out += ['', f'## {s["edge"]["title"]}', '', md(s['edge']['p'], c), '', f'## {t["title"]}', '',
            md(f'[{t["button"]["label"]}]({t["button"]["href"]})。{t["page"]}', c)]
    out += ['', f'## {s["license"]["title"]}', '', md(s['license']['p'], c), '']
    return '\n'.join(out)


def home(c):
    s = c['sections']
    cards = lambda items, cls: (f'    <div class="grid {cls}">\n' + '\n'.join(
        f'      <div class="card"><h3>{htm(i["h"], c)}</h3><p>{htm(i["p"], c)}</p></div>' for i in items) + '\n    </div>')
    main = [f'  <section>\n    <h2>{s["who"]["title"]}</h2>\n{cards(s["who"]["cards"], "who")}\n  </section>',
            f'  <section>\n    <h2>{s["features"]["title"]}</h2>\n    <ul class="features">\n' + '\n'.join(
                f'      <li><b>{htm(f["b"], c)}</b><span>{htm(f["p"], c)}</span></li>' for f in s['features']['items']) + '\n    </ul>\n  </section>',
            f'  <section>\n    <h2>{s["use"]["title"]}</h2>\n{cards(s["use"]["cards"], "use")}\n    <p class="keys">{htm(s["use"]["keys"], c)}</p>\n  </section>']
    mods = []
    for m in s['modules']['items']:
        part = [f'    <div class="module">', '      <div>', f'        <h3>{htm(m["name"], c)}<small>{htm(m["progress"], c)}</small></h3>',
                f'        <p>{htm(m["p"], c)}</p>']
        if m.get('stages'):
            part.append('        <div class="stages">' + ''.join(f'<span>{htm(t, c)}</span>' for t in m['stages']) + '</div>')
        part.append('      </div>')
        part.append(f'      <nav aria-label="{html.escape(m["name"])}">' + ''.join(
            f'<a href="{html.escape(link(n["href"], c, True))}">{htm(n["label"], c)}</a>' for n in m['nav']) + '</nav>')
        if 'demo' in m:
            d, v = m['demo'], html.escape(link(m['demo']['video'], c, True))
            part += ['      <figure class="demo">',
                     f'        <video controls playsinline preload="none" poster="{html.escape(link(d["poster"], c, True))}" width="1920" height="1080">'
                     f'<source src="{v}" type="video/mp4">你的浏览器播放不了这段视频，可以<a href="{v}">直接打开</a>。</video>',
                     f'        <p>{htm(d["caption"], c)}</p>', '      </figure>']
        mods.append('\n'.join(part + ['    </div>']))
    main.append(f'  <section>\n    <h2>{s["modules"]["title"]}</h2>\n' + '\n'.join(mods) + f'\n    <p class="later">{htm(s["modules"]["later"], c)}</p>\n  </section>')
    main.append(f'  <section>\n    <h2>{s["edge"]["title"]}</h2>\n    <p class="edge">{htm(s["edge"]["p"], c)}</p>\n  </section>')
    t = s['talk']
    main.append(f'  <section>\n    <h2>{t["title"]}</h2>\n    <div class="talk">\n      <p>{htm(t["page"], c)}</p>\n'
                f'      <a href="{html.escape(link(t["button"]["href"], c, True))}">{htm(t["button"]["label"], c)}</a>\n    </div>\n  </section>')
    actions = '\n'.join(f'      <a class="{b["class"]}" href="{html.escape(link(b["href"], c, True))}">▶ {htm(b["label"], c)}</a>' for b in c['buttons'])
    slots = {'title': html.escape(c['title']), 'title_html': '<br>'.join(html.escape(x) for x in c['title_lines']),
             'description': html.escape(c['description']), 'en': html.escape(c['en']), 'lead': htm(c['lead'], c),
             'actions': actions, 'more': htm(c['more'], c), 'main': '\n\n'.join(main),
             'footer': htm(s['license']['p'], c) + htm(s['license'].get('page_more', ''), c)}
    page = PAGE.read_text(encoding='utf-8')
    missing = set(re.findall(r'\{\{(\w+)\}\}', page)) - set(slots)
    assert not missing, f'home/page.html: no content for {", ".join(sorted(missing))}'
    return re.sub(r'\{\{(\w+)\}\}', lambda m: slots[m.group(1)], page)


def lessons_done():
    """How many lessons basics/course.json has made (an entry with an id)."""
    return sum(1 for item in json.loads((ROOT / 'basics' / 'course.json').read_text(encoding='utf-8')) if item.get('id'))


def made():
    # {lessons} in the text is how many lessons are made, from basics/course.json, so the count is never written by hand.
    c = json.loads(CONTENT.read_text(encoding='utf-8').replace('{lessons}', str(lessons_done())))
    return {README: readme(c), HOME: home(c)}


def write():
    if not CONTENT.exists():
        return False
    for path, text in made().items():
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8', newline='\n')
    return True


def check():
    """The README and the home page are what home/content.json makes; returns False when there is no content.json."""
    if not CONTENT.exists():
        return False
    stale = [p.relative_to(ROOT).as_posix() for p, text in made().items() if not p.exists() or p.read_text(encoding='utf-8') != text]
    assert not stale, f'{", ".join(stale)} differ from home/content.json: change the text there and run python3 tools/build.py (or tools/promo.py)'
    return True


if __name__ == '__main__':
    if '--check' in sys.argv[1:]:
        print('README.md and home/index.html match home/content.json' if check() else 'No home/content.json: nothing to check')
    else:
        print('Wrote README.md and home/index.html' if write() else 'No home/content.json: nothing written')
