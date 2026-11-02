#!/usr/bin/env python3
"""Check code, answers, claims and offline rules for every lesson. Standard library only."""
import ast
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'tools/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
HIDDEN_ROLES = ['学生小改写', '独立迁移']  # Students write these, so the answers must stay out of dist/.


def run(source, stdin):
    return subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', source], input=stdin.encode(), capture_output=True, timeout=5)


class Deck(HTMLParser):
    """Collect program text from <pre data-file> and every local link."""

    def __init__(self, text):
        super().__init__()
        self.shown, self.links, self.file, self.lines = [], [], None, []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'pre' and 'data-file' in attrs:
            self.file, self.lines = attrs['data-file'], []
        if self.file and tag == 'span' and 'ln' in (attrs.get('class') or '').split():
            self.lines.append('')
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag in ('script', 'link') and (attrs.get('src') or attrs.get('href')):
            raise AssertionError('External resource: ' + str(attrs))

    def handle_data(self, data):
        if self.file and self.lines:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == 'pre' and self.file:
            self.shown.append((self.file, '\n'.join(self.lines)))
            self.file = None


def check_programs(folder):
    scripts = sorted(folder.glob('starter/*.py')) + sorted(folder.glob('solutions/*.py'))
    for script in scripts:
        code = script.read_text(encoding='utf-8')
        assert '\t' not in code, f'Tab indentation: {script}'
        ast.parse(code, filename=str(script))
    cases = json.loads((folder / 'tests/contracts.json').read_text(encoding='utf-8'))
    covered = set()
    for case in cases:
        code = (folder / case['source']).read_text(encoding='utf-8')
        result = run(code, (folder / case['input']).read_text(encoding='utf-8'))
        assert result.returncode == 0, (case, result.stderr)
        assert result.stdout.decode().replace('\r\n', '\n') == (folder / case['expected']).read_text(encoding='utf-8'), f'Output mismatch: {case}'
        covered.add(case['source'])
    solutions = {p.relative_to(folder).as_posix() for p in folder.glob('solutions/*.py')}
    assert covered == solutions, f'Solutions without tests: {solutions - covered}'
    return len(scripts), len(cases)


def check_claims(folder):
    """Outputs and errors the slides promise must happen in real Python."""
    claims = json.loads((folder / 'tests/claims.json').read_text(encoding='utf-8'))
    for claim in claims:
        result = run(claim['code'], claim.get('stdin', ''))
        if 'error' in claim:
            assert result.returncode != 0 and claim['error'] in result.stderr.decode(), f'Claim failed: {claim}'
        else:
            assert result.returncode == 0 and result.stdout.decode().replace('\r\n', '\n') == claim['stdout'], f'Claim failed: {claim}'
    return len(claims)


def check_deck(lesson, folder):
    built = builder.DIST / lesson['id'] / 'index.html'
    text = built.read_text(encoding='utf-8')
    assert text == builder.render(lesson), f'Rebuild dist: {lesson["id"]}'
    assert not re.search(r'/Users/|/home/|[A-Za-z]:\\\\', text), 'Absolute path in deck'
    assert not re.search(r'@import|https?://[^"\')\s]+\.(?:js|css)\b', text), 'Remote resource in deck'
    deck = Deck(text)
    assert deck.shown, 'Deck shows no tested program'
    for file, code in deck.shown:
        assert code.strip() == (folder / file).read_text(encoding='utf-8').strip(), f'Slide code differs from {file}'
    pages = text.count('<section id="page-')
    tasks = json.loads((folder / 'tasks.json').read_text(encoding='utf-8'))
    for task in tasks:
        assert 1 <= task['page'] <= pages, f'Bad page: {task["id"]}'
        assert (folder / task['starter']).is_file() and (folder / task['solution']).is_file()
        if task['role'] in HIDDEN_ROLES:
            answer = (folder / task['solution']).read_text(encoding='utf-8').strip()
            assert answer not in text, f'Answer shown on slides: {task["solution"]}'
    for link in deck.links:
        parts = urlsplit(link)
        if not parts.scheme and parts.path:
            assert (built.parent / unquote(parts.path)).is_file(), f'Broken link: {link}'
    assert '<a class="ide' in text, 'Deck has no IDE link'
    return pages


def check_dist():
    assert not list(builder.DIST.rglob('solutions')) and not list(builder.DIST.rglob('tests')), 'Teacher material in dist'
    index = builder.DIST / 'index.html'
    text = index.read_text(encoding='utf-8')
    assert text == builder.render_index(builder.course()), 'Rebuild dist index'
    assert not re.search(r'/Users/|/home/', text), 'Absolute path in index'
    for link in re.findall(r'href="([^"]+)"', text):
        assert (index.parent / unquote(link)).exists(), f'Broken index link: {link}'


def check_docs():
    for doc in ROOT.rglob('*.md'):
        if {'.git', 'dist', 'node_modules', '.preview'} & set(doc.parts):
            continue
        for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', doc.read_text(encoding='utf-8')):
            if not link.startswith(('http:', 'https:')):
                assert (doc.parent / link).exists(), f'Broken link: {doc}: {link}'


def main():
    scripts = cases = claims = pages = 0
    lessons = builder.lessons()
    for lesson in lessons:
        folder = ROOT / 'lessons' / lesson['id']
        s, c = check_programs(folder)
        scripts += s; cases += c
        claims += check_claims(folder)
        pages += check_deck(lesson, folder)
    check_dist()
    check_docs()
    print(f'PASS: {len(lessons)} lesson(s), {pages} pages, {scripts} scripts, {cases} output cases, {claims} slide claims.')


if __name__ == '__main__':
    main()
