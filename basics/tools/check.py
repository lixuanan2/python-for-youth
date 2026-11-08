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
TEXT_FILES = {'.html', '.py', '.cpp', '.h', '.txt', '.md', '.json', '.js', '.css', '.csv'}
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
    # Newer clang refuses a chained comparison such as 60 <= x < 90; g++ and cpp.sh only warn, as lesson 5 shows.
    BUILT[source] = exe, subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-pedantic', '-Wno-error=parentheses', '-x', 'c++', '-', '-o', str(exe)],
                                        input=source.encode(), capture_output=True, timeout=60)
    return BUILT[source]


def run(source, stdin):
    if LANGUAGE == 'python':
        return subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', source], input=stdin.encode(), capture_output=True, timeout=5)
    exe, built = compile_cpp(source)
    if built.returncode:
        return built
    return subprocess.run([str(exe)], input=stdin.encode(), capture_output=True, timeout=5)


def compiles(source):
    if LANGUAGE == 'python':
        try:
            compile(source, 'page', 'exec')
            return True
        except SyntaxError:
            return False
    return compile_cpp(source)[1].returncode == 0


class Pages(HTMLParser):
    """The code each page hands the IDE, worked out the way deck.js does it."""

    def __init__(self, text):
        super().__init__()
        self.pages, self.lines = [], None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get('class') or '').split()
        if tag == 'section' and (attrs.get('id') or '').startswith('page-'):
            self.pages.append(dict(ide=attrs.get('data-ide'), full=None, lines=[], slots=0, button=False, code=None,
                                   steps=int(attrs.get('data-steps') or 1), changes=[]))
        if not self.pages:
            return
        page = self.pages[-1]
        if tag == 'pre' and 'code' in classes:
            self.lines = page['lines']
            if 'was' in classes:
                # The old version of a code change: shown first, never sent to the IDE.
                page['changes'].append(dict(old=[], old_file=attrs.get('data-file'), old_full=attrs.get('data-full'), new=None))
                self.lines = page['changes'][-1]['old']
            elif page['changes'] and page['changes'][-1]['new'] is None:
                change = page['changes'][-1]
                change.update(new=len(page['lines']), new_file=attrs.get('data-file'), new_full=attrs.get('data-full'),
                              at=attrs.get('data-change'))
            if page['full'] is None and 'was' not in classes:
                page['full'] = attrs.get('data-full')
        if self.lines is not None and tag == 'span' and 'ln' in classes:
            self.lines.append('')
        if self.lines is not None and tag == 'input' and 'slot' in classes and self.lines:
            assert self.lines is page['lines'] and not page['changes'], 'A code change cannot hold yellow boxes'
            page['slots'] += 1
            self.lines[-1] += attrs.get('value') or ''
        if tag == 'a' and 'ide' in classes and not page['button']:
            page['button'], page['code'] = True, attrs.get('data-code')

    def handle_data(self, data):
        if self.lines:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == 'pre' and self.lines is not None:
            page = self.pages[-1]
            change = page['changes'][-1] if page['changes'] else None
            if change and isinstance(change['new'], int) and self.lines is page['lines']:
                change['new'] = page['lines'][change['new']:]
            self.lines = None

    def ide_code(self, page):
        if page['code'] is not None:
            return page['code']
        return page['ide'] or page['full'] or '\n'.join(page['lines'])


def check_changes(text, folder):
    """Both versions of a code change are programs the page shows, so each must be tested: a data-file or a claim on that page."""
    claims = json.loads((folder / 'tests/claims.json').read_text(encoding='utf-8'))
    count = 0
    for number, page in enumerate(Pages(text).pages, 1):
        for change in page['changes']:
            where = f'{folder.name} page {number}'
            assert isinstance(change['new'], list) and change['new'], f'{where}: pre.code.was must be followed by the new version, a pre.code'
            assert change['at'] and 2 <= int(change['at']) <= page['steps'], f'{where}: the new version needs data-change, a step of this page from 2 on'
            for lines, file, full in ((change['old'], change['old_file'], change['old_full']),
                                      (change['new'], change.get('new_file'), change.get('new_full'))):
                code = '\n'.join(lines).strip()
                assert code, f'{where}: an empty version in a code change'
                # A page that shows only some lines (C++ often does) gives the whole program in data-full.
                whole = {code, (full or '').strip()} - {''}
                if not file:  # with data-file, check_deck compares the page with that tested file
                    assert any(c['page'] == number and c['code'].strip() in whole and ('stdout' in c or 'error' in c) for c in claims), \
                        f'{where}: a version of the code change without data-file needs a claim with its output in tests/claims.json'
            count += 1
    return count


def check_algos(text):
    """An algorithm demo plays a real run of the page's program: it must end where the program really ends."""
    count = 0
    for number, section in enumerate(re.findall(r'<section id="page-\d+".*?</section>', text, re.S), 1):
        found = builder.algo.Demos(section)
        for demo in found.demos:
            where = f'page {number}'
            data = json.loads(demo['trace'])
            steps, start, end = data['steps'], data['steps'][0], data['steps'][-1]
            code, first = found.program()
            assert data['language'] == LANGUAGE and data['first'] == first, f'{where}: rebuild the demo'
            result = run(code, demo['stdin'])
            assert result.returncode == 0 and result.stdout.decode().replace('\r\n', '\n') == end['out'], \
                f'{where}: the demo does not end with what the program prints'
            if data['kind'] == 'sort':
                assert sorted(end['list']) == sorted(start['list']), f'{where}: the sort lost or gained numbers'
                assert end['list'][-1] == max(start['list']), f'{where}: after a pass the biggest number must be last'
                assert not end['sorted'] or end['list'] == sorted(start['list']), f'{where}: the demo says sorted but is not'
            if data['kind'] == 'search':
                assert end['found'] and end['mid'] == end['target'], f'{where}: the search demo must find its number'
                assert all(s['lo'] <= s['target'] <= s['hi'] for s in steps), f'{where}: the number left the range'
            if data['kind'] == 'try':
                assert end['hits'] and all(s['hit'] == (s['left'] == s['right']) for s in steps if s['type'] == 'try'), \
                    f'{where}: the try demo must find an answer'
            lines = code.split('\n')
            assert all(s['line'] is None or 1 <= s['line'] <= len(lines) for s in steps), f'{where}: a step points at no line'
            shown = len(found.code)
            assert any(s['line'] and first <= s['line'] < first + shown for s in steps), f'{where}: no step runs a line the page shows'
            count += 1
    return count


def check_ide(text, folder):
    """What a page sends to the IDE must be a whole program, so the student can press Run."""
    claims = json.loads((folder / 'tests/claims.json').read_text(encoding='utf-8'))
    pages = Pages(text)
    hint = 'mark the whole program in tests/claims.json with "ide": true'
    for number, page in enumerate(pages.pages, 1):
        code = pages.ide_code(page).strip()
        assert not (page['ide'] and page['slots']), f'{folder.name} page {number} has yellow boxes, so its IDE code must follow them, not "ide"'
        if not code or any(c['page'] == number and c['code'].strip() == code for c in claims):
            continue  # nothing to send, or a claim already runs exactly this program
        if LANGUAGE == 'cpp':
            assert re.search(r'\bmain\s*\(', code), f'{folder.name} page {number} sends only part of a program to the IDE; {hint}'
        assert compiles(code), f'{folder.name} page {number} sends code that does not compile to the IDE; {hint}'
        if LANGUAGE == 'python':
            try:
                result = run(code, '')
            except subprocess.TimeoutExpired:
                continue
            assert b'NameError' not in result.stderr, f'{folder.name} page {number} sends code that uses a name it never sets; {hint}'


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
        if 'stdout' not in claim and 'error' not in claim:
            # A program that never stops, given to the IDE as it is: it only has to compile.
            assert claim.get('ide'), f'Claim without stdout or error: {claim}'
            assert compiles(claim['code']), f'IDE program does not compile: {claim}'
            continue
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
    check_ide(text, folder)
    changes = check_changes(text, folder)
    algos = check_algos(text)
    for file, code, lines in deck.shown:
        want = (folder / file).read_text(encoding='utf-8').strip()
        if lines:
            first, last = map(int, lines.split('-'))
            want = '\n'.join(want.split('\n')[first - 1:last]).strip()
        assert code.strip() == want, f'Slide code differs from {file}'
    pages = text.count('<section id="page-')
    attributes = [unquote(html.unescape(v)) for v in re.findall(r'="([^"]*)"', text)]
    shown = squash(html.unescape(re.sub(r'<[^>]+>', '', text)) + ''.join(attributes))
    tasks = json.loads((folder / 'tasks.json').read_text(encoding='utf-8'))
    for task in tasks:
        assert 1 <= task['page'] <= pages, f'Bad page: {task["id"]}'
        assert (folder / task['starter']).is_file() and (folder / task['solution']).is_file()
        if task['role'] in HIDDEN_ROLES:
            answer = (folder / task['solution']).read_text(encoding='utf-8').strip()
            escaped = html.escape(answer, quote=True).replace('\n', '&#10;')
            assert answer not in text and escaped not in text, f'Answer shown on slides: {task["solution"]}'
            # Spaces and line breaks may differ on a page, so compare with all whitespace removed,
            # in the visible text, in every attribute (IDE links carry code) and in every file given to students.
            key = squash(answer)
            assert key != squash((folder / task['starter']).read_text(encoding='utf-8')), f'Starter is the answer: {task["starter"]}'
            assert key not in shown, f'Answer shown on slides: {task["solution"]}'
            for file in built.parent.rglob('*'):
                if file.is_file() and file.suffix in TEXT_FILES and file != built:
                    given = file.read_text(encoding='utf-8')
                    for form in (given, html.unescape(given)):
                        assert key not in squash(form), f'Answer in {file.relative_to(builder.DIST)}'
    for link in deck.links:
        parts = urlsplit(link)
        if not parts.scheme and parts.path:
            assert (built.parent / unquote(parts.path)).is_file(), f'Broken link: {link}'
    assert '<a class="ide' in text, 'Deck has no IDE link'
    return pages, changes, algos


def squash(text):
    return re.sub(r'\s+', '', text)


def check_dist():
    assert not list(builder.DIST.rglob('solutions')) and not list(builder.DIST.rglob('tests')), 'Teacher material in dist'
    index = builder.DIST / 'index.html'
    text = index.read_text(encoding='utf-8')
    assert text == builder.render_index(builder.course()), 'Rebuild dist index'
    assert not re.search(r'/Users/|/home/', text), 'Absolute path in index'
    links = local_links(index)
    for lesson in builder.lessons():
        page = builder.DIST / lesson['id'] / 'starter' / 'index.html'
        assert page.is_file() and page.read_text(encoding='utf-8') == builder.render_starter(lesson), f'Rebuild dist starter page: {lesson["id"]}'
        links += local_links(page)
    return len(links)


def local_links(page):
    """Every local link must open a file: GitHub Pages lists no folders, so a link to one is a 404 online."""
    text = page.read_text(encoding='utf-8')
    assert not re.search(r'/Users/|/home/|[A-Za-z]:\\\\', text), f'Absolute path in {page.relative_to(builder.DIST)}'
    links = []
    for link in re.findall(r'href="([^"]+)"', text):
        parts = urlsplit(html.unescape(link))
        if parts.scheme or not parts.path:
            continue
        target = (page.parent / unquote(parts.path)).resolve()
        assert target.is_relative_to(builder.DIST.resolve()), f'Link leaves dist: {page.relative_to(builder.DIST)}: {link}'
        assert target.is_file(), f'Link to a folder or a missing file: {page.relative_to(builder.DIST)}: {link}'
        links.append(link)
    return links


def check_docs():
    """Every Markdown link in the whole repository opens a file in it: someone who clones only this repository has nothing else."""
    repo = ROOT.parent.resolve()
    count = 0
    for doc in repo.rglob('*.md'):
        if {'.git', 'dist', 'node_modules', '.preview'} & set(doc.relative_to(repo).parts):
            continue
        name = doc.relative_to(repo).as_posix()
        for link in re.findall(r'\]\(<?([^)#>\s]*)>?(?:#[^)\s]*)?(?:\s+"[^"]*")?\)', doc.read_text(encoding='utf-8')):
            if not link or urlsplit(link).scheme:
                continue
            target = (doc.parent / unquote(link)).resolve()
            assert target.is_relative_to(repo), f'Link leaves the repository: {name}: {link}'
            assert target.exists(), f'Broken link: {name}: {link}'
            count += 1
    return count


def main():
    scripts = cases = claims = pages = changes = algos = 0
    lessons = builder.lessons()
    for lesson in lessons:
        folder = ROOT / 'lessons' / lesson['id']
        s, c = check_programs(folder)
        scripts += s; cases += c
        claims += check_claims(folder)
        p, c, a = check_deck(lesson, folder)
        algos += a
        pages += p; changes += c
    links = check_dist()
    stale = [lesson['id'] for lesson in builder.stale_pdfs()]
    assert not stale, f'PDF older than its deck, run python3 tools/build.py --pdf: {", ".join(stale)}'
    docs = check_docs()
    print(f'PASS: {len(lessons)} lesson(s), {pages} pages, {scripts} scripts, {cases} output cases, {claims} slide claims, {changes} code changes, {algos} algorithm demos, {links} index and starter links, {docs} document links.')


if __name__ == '__main__':
    main()
