"""Algorithm demos: run the program on the page with a line tracer, then turn the run into steps for the player.

The page shows the program; build.py runs exactly that text with real Python and writes the steps into the page,
so the animation can never disagree with the code. tools/check.py runs it again and checks the end result.
Standard library only.
"""
import html
from html.parser import HTMLParser
import json
import re
import subprocess
import sys

KINDS = ('sort', 'search', 'try')
# The variables each kind of demo watches, named by data- attributes on div.algo.
ROLES = {'sort': ('list',), 'search': ('lo', 'hi', 'mid', 'target'), 'try': ('var',)}
MAX_EVENTS = 4000
MAX_STEPS = 60

# Runs in a child process: the program reads the given input, and every line it reaches is recorded with the
# simple values in scope (whole numbers, words, lists of them) and what it has printed so far.
TRACER = r'''
import io, json, sys
code, stdin = json.loads(sys.stdin.read())
sys.stdin = io.StringIO(stdin)
out = io.StringIO()
events = []
def simple(v):
    return isinstance(v, (bool, int, str)) or (isinstance(v, list) and all(isinstance(x, (bool, int, str)) for x in v))
def note(frame, line):
    if len(events) > %d:
        raise RuntimeError('too many steps')
    names = {k: (list(v) if isinstance(v, list) else v) for k, v in frame.f_locals.items() if not k.startswith('__') and simple(v)}
    events.append([line, names, out.getvalue()])
def trace(frame, event, arg):
    if frame.f_code.co_filename != '<algo>':
        return None
    if event == 'line':
        note(frame, frame.f_lineno)
    elif event == 'return' and frame.f_back is not None and frame.f_back.f_code.co_filename != '<algo>':
        note(frame, None)
    return trace
real = sys.stdout
sys.stdout = out
sys.settrace(trace)
try:
    exec(compile(code, '<algo>', 'exec'), {'__name__': '__main__'})
finally:
    sys.settrace(None)
    sys.stdout = real
print(json.dumps(events, ensure_ascii=False))
''' % MAX_EVENTS


def run(code, stdin):
    """Every line the program reaches, in order: [line, values, printed so far]; the last entry is the end (line None)."""
    result = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', TRACER], input=json.dumps([code, stdin]).encode(),
                            capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    return json.loads(result.stdout)


def condition(source):
    """The test of an if line, without if and the colon."""
    match = re.fullmatch(r'\s*(?:if|elif)\s+(.*):\s*', source)
    return match and match.group(1)


def value(expr, names):
    return eval(expr, {'__builtins__': {}}, dict(names))


def steps(kind, code, stdin, names):
    """The run as player steps. names maps a role to the variable on the page, such as {"list": "a"}."""
    assert kind in KINDS, f'data-algo must be one of {", ".join(KINDS)}'
    lines = code.split('\n')
    events = run(code, stdin)
    make = {'sort': sort_steps, 'search': search_steps, 'try': try_steps}[kind]
    found = make(lines, events, names)
    if kind == 'sort':
        assert 4 <= len(found[0]['list']) <= 8, 'a sort demo needs 4 to 8 numbers, so the bars stay readable on a projector'
    else:
        low, high = found[0]['range']
        assert 2 <= high - low + 1 <= 100, 'a range demo shows 2 to 100 numbers'
    assert 3 <= len(found) <= MAX_STEPS, f'an algorithm demo needs 3 to {MAX_STEPS} steps, this one has {len(found)}'
    assert found[-1]['out'] == events[-1][2], 'the demo must end with everything the program printed'
    return found


def moves(events):
    """Pairs of (what a line saw before it ran, what it left behind)."""
    return [(events[k], events[k + 1]) for k in range(len(events) - 1)]


def printed(before, after):
    return after[2][len(before[2]):]


def sort_steps(lines, events, names):
    """Compare two neighbours, swap them, print: every list change is a swap the player can animate."""
    name = names['list']
    steps = []
    for before, after in moves(events):
        line, now, new = before[0], before[1], after[1]
        test = condition(lines[line - 1])
        if test and f'{name}[' in test:
            places = re.findall(re.escape(name) + r'\[([^\]]+)\]', test)
            names.setdefault('at', places)
            spots = [value(i, now) for i in places]
            assert len(spots) == 2, f'the compare line must name two places in {name}: {lines[line - 1].strip()}'
            op = re.search(r'\]\s*(<=|>=|<|>)\s*' + re.escape(name), test)
            assert op, f'the compare line must compare {name}[…] with {name}[…] using < or >: {lines[line - 1].strip()}'
            if not steps:
                steps.append(dict(type='start', line=None, list=now[name], out=before[2]))
            steps.append(dict(type='compare', line=line, list=now[name], at=spots, op=op.group(1),
                              swap=bool(value(test, now)), out=before[2]))
        elif steps and name in new and new[name] != now[name]:
            changed = [i for i, (x, y) in enumerate(zip(now[name], new[name])) if x != y]
            assert len(changed) == 2 and sorted(now[name]) == sorted(new[name]), f'a sort demo can only swap two places at a time (line {line})'
            steps.append(dict(type='swap', line=line, list=new[name], at=changed, out=after[2]))
        elif steps and printed(before, after):
            steps.append(dict(type='print', line=line, list=new.get(name, now[name]), text=printed(before, after), out=after[2]))
    assert steps, f'no line compares two places in {name}'
    final = steps[-1]['list']
    steps.append(dict(type='end', line=None, list=final, sorted=final == sorted(final), out=events[-1][2]))
    # A place is settled once no later step touches it and everything after it already holds its sorted value.
    goal = sorted(final)
    for k, step in enumerate(steps):
        later = {i for s in steps[k + 1:] for i in s.get('at', [])}
        done = []
        for i in range(len(final) - 1, -1, -1):
            if i in later or step['list'][i] != goal[i]:
                break
            done.append(i)
        step['done'] = sorted(done)
    return steps


def search_steps(lines, events, names):
    """Guess the middle, then keep the half that can still hold the answer, until the guess is right."""
    lo, hi, mid, target = names['lo'], names['hi'], names['mid'], names['target']
    steps = []
    for before, after in moves(events):
        line, now, new = before[0], before[1], after[1]
        if not steps and all(n in now for n in (lo, hi, target)):
            steps.append(dict(type='start', line=None, lo=now[lo], hi=now[hi], target=now[target], out=before[2]))
        if not steps:
            continue
        common = dict(lo=new.get(lo), hi=new.get(hi), mid=new.get(mid), target=new.get(target), out=after[2])
        if new.get(mid) != now.get(mid) and isinstance(new.get(mid), int) and now[lo] <= new[mid] <= now[hi]:
            steps.append(dict(type='pick', line=line, before=[now[lo], now[hi]], **common))
        elif new.get(lo) != now.get(lo):
            steps.append(dict(type='lo', line=line, **common))
        elif new.get(hi) != now.get(hi):
            steps.append(dict(type='hi', line=line, **common))
        elif printed(before, after):
            steps[-1]['out'] = after[2]  # the guess is printed right after it is made
    assert steps, f'{lo}, {hi} and {target} never all have a value'
    last = events[-1][1]
    picks = sum(s['type'] == 'pick' for s in steps)
    steps.append(dict(type='end', line=None, lo=last[lo], hi=last[hi], mid=last.get(mid), target=last[target],
                      found=last.get(mid) == last[target], count=picks, out=events[-1][2]))
    steps[0]['range'] = [steps[0]['lo'], steps[0]['hi']]
    return steps


def try_steps(lines, events, names):
    """Try every value in turn and check it: each pass over the if line is one try."""
    var = names['var']
    steps = []
    for before, after in moves(events):
        line, now = before[0], before[1]
        test = condition(lines[line - 1])
        if test and var in now:
            parts = re.fullmatch(r'(.+?)\s*==\s*(.+)', test)
            assert parts, f'the check of a try demo must be A == B: {lines[line - 1].strip()}'
            if not steps:
                steps.append(dict(type='start', line=None, out=before[2]))
            steps.append(dict(type='try', line=line, value=now[var], hit=bool(value(test, now)),
                              left=value(parts.group(1), now), right=value(parts.group(2), now), out=before[2]))
        elif steps and printed(before, after):
            steps[-1]['out'] = after[2]  # what a right answer prints belongs to its try
            steps[-1]['text'] = printed(before, after)
    assert steps, f'no if line runs while {var} has a value'
    tried = [s['value'] for s in steps if s['type'] == 'try']
    steps[0]['range'] = [min(tried), max(tried)]
    steps.append(dict(type='end', line=None, count=len(tried), hits=[s['value'] for s in steps if s.get('hit')],
                      out=events[-1][2]))
    return steps


class Demos(HTMLParser):
    """The algorithm demos of one page, and the program in the page's code editor."""

    def __init__(self, text):
        super().__init__()
        self.demos, self.lines, self.code = [], None, None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get('class') or '').split()
        if tag == 'div' and 'algo' in classes:
            kind = attrs.get('data-algo')
            assert kind in KINDS, f'data-algo must be one of {", ".join(KINDS)}'
            roles = {role: attrs.get(f'data-{role}') for role in ROLES[kind]}
            assert all(roles.values()), f'a {kind} demo needs ' + ', '.join(f'data-{r}' for r in ROLES[kind])
            self.demos.append(dict(kind=kind, names=roles, stdin=attrs.get('data-stdin') or '', trace=attrs.get('data-trace')))
        if tag == 'pre' and 'code' in classes and 'was' not in classes and self.code is None:
            self.code = self.lines = []
        if self.lines is not None and tag == 'span' and 'ln' in classes:
            self.lines.append('')

    def handle_data(self, data):
        if self.lines:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.lines = None


def demos(section):
    """Each demo of a page with its steps: the program is the text of the page's code editor, run for real."""
    found = Demos(section)
    assert not found.demos or found.code, 'an algorithm demo needs its program in a pre.code on the same page'
    code = '\n'.join(found.code or [])
    for demo in found.demos:
        names = dict(demo['names'])
        demo['code'] = code
        demo['data'] = dict(kind=demo['kind'], names=names, steps=steps(demo['kind'], code, demo['stdin'], names))
    return found.demos


def encode(data):
    return html.escape(json.dumps(data, ensure_ascii=False, separators=(',', ':')), quote=True)


def embed(slides):
    """Write the steps into the div.algo of every built page, as data-trace."""
    def page(match):
        section = match.group(0)
        found = demos(section)
        if not found:
            return section
        assert len(found) == 1, 'one algorithm demo per page'
        assert 'data-steps=' not in section.split('>', 1)[0], 'a page with an algorithm demo uses its player, not data-steps'
        return section.replace('<div class="algo"', f'<div class="algo" data-trace="{encode(found[0]["data"])}"', 1)
    return re.sub(r'<section id="page-\d+".*?</section>', page, slides, flags=re.S)


if __name__ == '__main__':
    kind, file, stdin = sys.argv[1], sys.argv[2], sys.argv[3].encode().decode('unicode_escape')
    roles = dict(pair.split('=') for pair in sys.argv[4:])
    for s in steps(kind, open(file, encoding='utf-8').read().rstrip('\n'), stdin, roles):
        print(json.dumps(s, ensure_ascii=False))
