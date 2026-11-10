"""Hand-written trace pages: the lines a page lights step by step must follow a real run of its program.

A trace page has data-steps and a pre.code whose lines carry l1, l2 … (lit at that step). For each step with lit
lines, the run must reach every lit line in one stretch, and the stretches go forward through the run in step
order. A stretch may start where the last one started, because a page often spends two steps on one line (the
left side of an and, then the right side). A box that names a variable (<i>i</i><b>2</b>, or <i>i = 2</i>) must
hold that value somewhere in the stretch of the step it first shows on, which also pins which pass of a loop a
step means. Values are checked for Python only.

The program is the whole one even when the page shows a few lines: data-full (from data-file and data-lines),
the page's data-ide, or the page's own lines. Its input comes from data-stdin on the pre.code, or else from the
claims of that page that run the same program; with several inputs, a page may move on to the next input
partway, as a page that first types 12 and then types 十二 does.
Standard library only.
"""
from html.parser import HTMLParser
import json
import re
import sys

import algo

LIMIT = 20000
# Lines that never run on their own: else:, braces, and in C++ #include and using.
STRUCTURE = re.compile(r'else\s*:|\}|\{|\}?\s*else\s*\{?|#.*|using\s.*|')  # matching tries per page, so a hopeless page fails fast


class Page(HTMLParser):
    """The code editors of a page, their lit lines, and the boxes that name values."""

    def __init__(self, section):
        super().__init__(convert_charrefs=True)
        self.pres, self.boxes, self.row, self.box, self.part = [], [], None, None, None
        self.depth = 0
        self.feed(section)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get('class') or '').split()
        if tag == 'pre' and 'code' in classes:
            self.pres.append(dict(attrs=attrs, was='was' in classes, pick='pick' in classes, rows=[]))
            self.row = None
        elif tag == 'span' and 'ln' in classes and self.pres and self.row is None and self.part is None:
            lit = {int(c[1:]) for c in classes if re.fullmatch(r'l\d', c)}
            self.pres[-1]['rows'].append(dict(text='', lit=lit))
            self.row, self.depth = self.pres[-1]['rows'][-1], 0
        elif tag == 'span' and self.row is not None:
            self.depth += 1
        elif tag == 'input' and self.row is not None:
            self.row['text'] += attrs.get('value') or ''
        elif tag == 'div' and 'box' in classes:
            self.box = dict(step=first_step(classes), label='', value='')
        elif tag in ('i', 'b') and self.box is not None:
            self.part = 'label' if tag == 'i' else 'value'

    def handle_endtag(self, tag):
        if tag == 'span' and self.row is not None:
            if self.depth:
                self.depth -= 1
            else:
                self.row = None
        elif tag == 'pre':
            self.row = None
        elif tag in ('i', 'b'):
            self.part = None
        elif tag == 'div' and self.box is not None:
            self.boxes.append(self.box)
            self.box = None

    def handle_data(self, data):
        if self.row is not None:
            self.row['text'] += data
        elif self.box is not None and self.part:
            self.box[self.part] += data


def first_step(classes):
    """The first step a part of the page shows on."""
    for c in classes:
        if re.fullmatch(r'(?:s|only)\d', c):
            return int(re.sub(r'\D', '', c))
    return 1


def reads_input(code, language):
    return 'input(' in code if language == 'python' else bool(re.search(r'\bcin\b|scanf|getline', code))


def program_of(pre, section, language):
    """The whole program a pre.code belongs to, and the program line of its first row (or None)."""
    rows = [r['text'] for r in pre['rows']]
    attrs = pre['attrs']
    whole = attrs.get('data-full')
    if whole is None:
        ide = re.search(r'<section[^>]*\bdata-ide="([^"]*)"', section)
        whole = html_unescape(ide.group(1)) if ide and not pre['was'] else None
    if whole is None:
        whole = '\n'.join(rows)
    whole = whole.rstrip('\n')
    lines = whole.split('\n')
    if attrs.get('data-lines'):
        first = int(attrs['data-lines'].split('-')[0])
    else:  # find the rows as one block of the program
        first = next((k + 1 for k in range(len(lines) - len(rows) + 1)
                      if [l.rstrip() for l in lines[k:k + len(rows)]] == [r.rstrip() for r in rows]), None)
    if language == 'cpp' and not re.search(r'\bmain\s*\(', whole):
        return whole, None
    return whole, first


def html_unescape(text):
    import html
    return html.unescape(text)


def bodies(code, language):
    """For each line that starts a function, the program lines of its body."""
    lines = code.split('\n')
    found = {}
    for k, line in enumerate(lines):
        if language == 'python' and re.match(r'\s*def\s', line):
            indent = len(line) - len(line.lstrip())
            body = []
            for j in range(k + 1, len(lines)):
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent:
                    break
                body.append(j + 1)
            found[k + 1] = set(body)
        if language == 'cpp' and re.match(r'(?!\s*(?:if|for|while|switch|return|else)\b)\s*[\w:<>,*&\s]+?\b\w+\s*\([^;]*\)\s*\{', line) \
                and len(line) == len(line.lstrip()):
            depth, body = 0, []
            for j in range(k, len(lines)):
                text = algo.masked(lines[j])
                depth += text.count('{') - text.count('}')
                if j > k:
                    body.append(j + 1)
                if depth == 0 and j > k:
                    break
            found[k + 1] = set(body)
    return found


def matches(value, text):
    """Does a value read the way the page writes it? A box may list several values (1, 2, 3) or wrap one in [ ]."""
    text, shown = text.strip(), str(value)
    if shown == text or shown == text.strip('"\'“”'):
        return True
    if isinstance(value, str):
        return bool(value.strip()) and value in text
    return shown in re.split(r'[\s,，、→]+', text)


def wanted(boxes, step, names):
    """The values a step's boxes promise: {name: text} for boxes labelled with a variable of the program."""
    found = {}
    for box in boxes:
        if box['step'] != step:
            continue
        label = box['label'].strip()
        same = re.fullmatch(r'([A-Za-z_]\w*)\s*=\s*(\S+)', label)
        if same and same.group(1) in names:
            found[same.group(1)] = same.group(2)
        elif re.fullmatch(r'[A-Za-z_]\w*', label) and label in names and box['value'].strip():
            found[label] = box['value'].strip()
    return found


def follow(steps, runs):
    """Place every step on a stretch of a run, in order; return None, or the step that cannot be placed.

    A step's values may show anywhere from where its stretch starts until the next step starts (a value is often
    ready only after the lit line has called a function or finished a loop); the last step's until the run ends."""
    tries, blame = [0], [(0, 'line')]

    def holds(want, events):
        return all(not any(name in e[1] for e in events) or any(name in e[1] and matches(e[1][name], text) for e in events)
                   for name, text in want.items())

    def place(k, run, start, used, before):
        tries[0] += 1
        if tries[0] > LIMIT:
            return False
        events = runs[run]
        if k == len(steps):
            if before is None or holds(before[2], runs[before[3]][before[0]:]):
                return True
            blame[0] = max(blame[0], (k - 1, 'value'))
            return False
        lit, stretched = steps[k][1], False
        for a in range(start, len(events)):
            if events[a][0] not in lit:
                continue
            seen, b = set(), a
            while b < len(events) and not lit <= seen:
                seen.add(events[b][0])
                b += 1
            if not lit <= seen:
                break
            while b < len(events) and events[b][0] in lit:  # the stretch goes on while lit lines keep running
                b += 1
            stretched = True
            if before is not None and before[3] == run and not holds(before[2], events[before[0]:max(before[1], a) + 1]):
                blame[0] = max(blame[0], (k - 1, 'value'))
                continue
            if place(k + 1, run, a, used, (a, b, steps[k][2], run)):
                return True
        if not stretched:
            blame[0] = max(blame[0], (k, 'line'))
        # Move on to another input from its beginning, as a page does when it types something else.
        if before is None or holds(before[2], runs[before[3]][before[0]:]):
            for other in range(len(runs)):
                if other not in used and place(k, other, 0, used | {other}, None):
                    return True
        return False

    for run in range(len(runs)):
        if place(0, run, 0, {run}, None):
            return None
    return steps[blame[0][0]][0], blame[0][1]


def check(section, number, claims, language):
    """('checked' | 'skipped' | 'wrong', note) for one page."""
    head = section.split('>', 1)[0]
    total = re.search(r'data-steps="(\d+)"', head)
    if not total:
        return None
    page = Page(section)
    pres = [p for p in page.pres if any(r['lit'] for r in p['rows']) and not p['pick']]
    if not pres:
        return None
    change = next((int(p['attrs']['data-change']) for p in page.pres if p['attrs'].get('data-change')), None)
    newer = next((p for p in page.pres if p['attrs'].get('data-change')), None)
    if change:  # the old version is checked too when only the new rows are lit
        pres = [p for p in page.pres if not p['pick'] and (any(r['lit'] for r in p['rows']) or p['was'])]
    notes, checked = [], False
    for pre in pres:
        code, first = program_of(pre, section, language)
        if first is None:
            notes.append('the lines on the page are not part of a whole program it can run')
            continue
        stdins = [pre['attrs']['data-stdin']] if pre['attrs'].get('data-stdin') is not None else \
            [c.get('stdin', '') for c in claims if c['page'] == number and c['code'].strip() == code.strip()]
        if not stdins:
            if reads_input(code, language):
                notes.append('the program reads input: add data-stdin to the pre.code, or a claim with stdin')
                continue
            stdins = ['']
        lines = code.split('\n')
        functions = bodies(code, language)
        steps = []
        for step in range(1, int(total.group(1)) + 1):
            if change and (pre['was'] != (step < change)):
                continue  # in a code change, the old version owns the steps before the change, the new one the rest
            # else: and a brace alone never run as a line of their own, so lighting them asks for nothing.
            lit = {first + k for k, r in enumerate(pre['rows']) if step in r['lit'] and not STRUCTURE.fullmatch(r['text'].strip())}
            if pre['was'] and newer:  # a page may light the old version's steps on the new rows (they are one editor)
                texts = [r['text'].strip() for r in pre['rows']]
                for r in newer['rows']:
                    if step in r['lit'] and texts.count(r['text'].strip()) == 1 and not STRUCTURE.fullmatch(r['text'].strip()):
                        lit.add(first + texts.index(r['text'].strip()))
            for start, body in functions.items():
                if start in lit:
                    lit -= body  # a whole function lit at once is its definition: only the def line runs
            if lit:
                steps.append((step, lit))
        # data-point="4" marks steps that point at lines (input is read twice: here and here) instead of
        # following the run; their lines only have to run somewhere.
        pointing = {int(n) for n in re.findall(r'\d+', pre['attrs'].get('data-point') or '')}
        try:
            runs = [algo.line_runs(code, stdin, language) for stdin in dict.fromkeys(stdins)]
        except AssertionError as failed:
            notes.append('the traced copy of the program does not build: ' + str(failed).split('\n')[1:2][0][:120])
            continue
        reached = {line for run in runs for line, _ in run}
        for step, lit in steps:
            if step in pointing and not lit <= reached:
                return 'wrong', f'step {step} points at a line no run reaches: ' + ', '.join(str(n) for n in sorted(lit - reached))
        steps = [(step, lit) for step, lit in steps if step not in pointing]
        if not steps:
            continue
        names = {n for run in runs for _, values in run for n in values}
        steps = [(step, lit, wanted(page.boxes, step, names) if language == 'python' else {}) for step, lit in steps]
        stuck = follow(steps, runs)
        if stuck is not None:
            stuck, why = stuck
            lit = next(l for s, l, _ in steps if s == stuck)
            want = next(w for s, _, w in steps if s == stuck)
            shown = '; '.join(f'line {n}: {lines[n - 1].strip()}' for n in sorted(lit))
            if why == 'value':
                values = ', '.join(f'{k} = {v}' for k, v in want.items())
                return 'wrong', f'step {stuck} shows {values}, but the run never has that while it is at {shown}'
            return 'wrong', f'step {stuck} lights {shown}, which the run does not reach after the steps before it'
        checked = True
    if checked:
        return 'checked', ''
    return 'skipped', '; '.join(dict.fromkeys(notes)) or 'nothing to check'


def check_deck(text, claims, language):
    """Every trace page of a built deck: (checked count, [(page, note)] skipped, [(page, note)] wrong)."""
    checked, skipped, wrong = 0, [], []
    for number, section in enumerate(re.findall(r'<section id="page-\d+".*?</section>', text, re.S), 1):
        result = check(section, number, claims, language)
        if result is None:
            continue
        kind, note = result
        if kind == 'checked':
            checked += 1
        elif kind == 'skipped':
            skipped.append((number, note))
        else:
            wrong.append((number, note))
    return checked, skipped, wrong


if __name__ == '__main__':
    print(json.dumps(Page(sys.stdin.read()).pres, ensure_ascii=False, indent=1))
