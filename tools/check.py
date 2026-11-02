#!/usr/bin/env python3
"""Check code, answers, claims and offline rules for every lesson. Standard library only."""
import ast
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'tools/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
HIDDEN_ROLES = ['学生小改写', '独立迁移']  # Students write these, so the answers must stay out of dist/.


LANGUAGE = builder.site()['language']
SUFFIX = {'python': '.py', 'cpp': '.cpp'}[LANGUAGE]
WORK = tempfile.TemporaryDirectory(prefix='lesson-check-')
BUILT = {}


def find_compiler():
    compiler = os.environ.get('CXX') or shutil.which('clang++') or shutil.which('g++')
    assert compiler, 'No C++ compiler found'
    return compiler


def error_text(claim):
    """Compilers word errors differently, so a C++ claim may give the text for each one."""
    want = claim['error']
    if isinstance(want, str):
        return want
    version = subprocess.run([find_compiler(), '--version'], capture_output=True, text=True).stdout
    return want['clang' if 'clang' in version else 'gcc']


def compile_cpp(source):
    """Compile C++11 once per program; a failed compile comes back as the result."""
    if source in BUILT:
        return BUILT[source]
    compiler = find_compiler()
    exe = Path(WORK.name) / (hashlib.sha256(source.encode()).hexdigest()[:16] + ('.exe' if os.name == 'nt' else ''))
    BUILT[source] = exe, subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-pedantic', '-x', 'c++', '-', '-o', str(exe)],
                                        input=source.encode(), capture_output=True, timeout=60)
    return BUILT[source]


def run(source, stdin):
    if LANGUAGE == 'python':
        return subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', source], input=stdin.encode(), capture_output=True, timeout=5)
    exe, built = compile_cpp(source)
    if built.returncode:
        return built
    return subprocess.run([str(exe)], input=stdin.encode(), capture_output=True, timeout=5)


class Deck(HTMLParser):
    """Collect program text from <pre data-file> and every local link."""

    def __init__(self, text):
        super().__init__()
        self.shown, self.links, self.file, self.lines = [], [], None, []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'pre' and 'data-file' in attrs:
            self.file, self.lines, self.range = attrs['data-file'], [], attrs.get('data-lines')
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
            self.shown.append((self.file, '\n'.join(self.lines), self.range))
            self.file = None


def check_programs(folder):
    scripts = sorted(folder.glob(f'starter/*{SUFFIX}')) + sorted(folder.glob(f'solutions/*{SUFFIX}'))
    for script in scripts:
        code = script.read_text(encoding='utf-8')
        assert '\t' not in code, f'Tab indentation: {script}'
        if LANGUAGE == 'python':
            ast.parse(code, filename=str(script))
        else:
            built = compile_cpp(code)[1]
            assert built.returncode == 0 and not built.stderr, f'{script}: {built.stderr.decode()}'
    cases = json.loads((folder / 'tests/contracts.json').read_text(encoding='utf-8'))
    covered = set()
    for case in cases:
        code = (folder / case['source']).read_text(encoding='utf-8')
        result = run(code, (folder / case['input']).read_text(encoding='utf-8'))
        assert result.returncode == 0, (case, result.stderr)
        assert result.stdout.decode().replace('\r\n', '\n') == (folder / case['expected']).read_text(encoding='utf-8'), f'Output mismatch: {case}'
        covered.add(case['source'])
    solutions = {p.relative_to(folder).as_posix() for p in folder.glob(f'solutions/*{SUFFIX}')}
    assert covered == solutions, f'Solutions without tests: {solutions - covered}'
    return len(scripts), len(cases)


def check_claims(folder):
    """Outputs and errors the slides promise must happen in real Python."""
    claims = json.loads((folder / 'tests/claims.json').read_text(encoding='utf-8'))
    for claim in claims:
        result = run(claim['code'], claim.get('stdin', ''))
        if 'error' in claim:
            # GCC prints curly quotes in a UTF-8 locale and straight ones elsewhere, such as on Windows.
            stderr = result.stderr.decode(errors='replace').replace('‘', "'").replace('’', "'")
            assert result.returncode != 0 and error_text(claim) in stderr, f'Claim failed: {claim}\n{stderr}'
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
    for file, code, lines in deck.shown:
        want = (folder / file).read_text(encoding='utf-8').strip()
        if lines:
            first, last = map(int, lines.split('-'))
            want = '\n'.join(want.split('\n')[first - 1:last]).strip()
        assert code.strip() == want, f'Slide code differs from {file}'
    pages = text.count('<section id="page-')
    tasks = json.loads((folder / 'tasks.json').read_text(encoding='utf-8'))
    for task in tasks:
        assert 1 <= task['page'] <= pages, f'Bad page: {task["id"]}'
        assert (folder / task['starter']).is_file() and (folder / task['solution']).is_file()
        if task['role'] in HIDDEN_ROLES:
            answer = (folder / task['solution']).read_text(encoding='utf-8').strip()
            escaped = html.escape(answer, quote=True).replace('\n', '&#10;')
            assert answer not in text and escaped not in text, f'Answer shown on slides: {task["solution"]}'
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
        if {'.git', 'dist', 'node_modules', '.preview'} & set(doc.relative_to(ROOT).parts):
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
