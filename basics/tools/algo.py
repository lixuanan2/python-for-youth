"""Algorithm demos: run the program on the page with a line tracer, then turn the run into steps for the player.

The page shows the program; build.py runs exactly that program and writes the steps into the page, so the
animation can never disagree with the code. tools/check.py runs it again and checks the end result.
Python is traced with sys.settrace. C++ is copied with a trace call put before each statement of main, compiled
with the same compiler the checks use, and run: the calls print each line and the variables in scope.
Standard library only.
"""
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

KINDS = ('sort', 'search', 'try')
# The variables each kind of demo watches, named by data- attributes on div.algo.
ROLES = {'sort': ('list',), 'search': ('lo', 'hi', 'mid', 'target'), 'try': ('var',)}
# A C++ array is longer than the numbers in it, so data-size names the variable that says how many are used.
OPTIONAL = {'sort': ('size',), 'search': (), 'try': ()}
MAX_EVENTS = 4000
MAX_STEPS = 60

# Runs in a child process: the program reads the given input, and every line it reaches is recorded with the
# simple values in scope (whole numbers, words, lists of them) and what it has printed so far.
TRACER = r'''
import io, json, sys
code, stdin, lines = json.loads(sys.stdin.read())
sys.stdin = io.StringIO(stdin)
import random
random.seed(0)
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
    elif event == 'call' and lines and frame.f_code.co_name != '<module>':
        note(frame, frame.f_code.co_firstlineno)  # a call runs the def line again, as a page lights it
    elif event == 'return' and frame.f_back is not None and frame.f_back.f_code.co_filename != '<algo>':
        note(frame, None)
    elif event == 'return' and lines and frame.f_back is not None:
        note(frame.f_back, frame.f_back.f_lineno)  # the calling line goes on once the call comes back
    return trace
real = sys.stdout
sys.stdout = out
sys.settrace(trace)
try:
    exec(compile(code, '<algo>', 'exec'), {'__name__': '__main__'})
except BaseException:
    if not lines:
        raise
finally:
    sys.settrace(None)
    sys.stdout = real
print(json.dumps(events, ensure_ascii=False))
''' % MAX_EVENTS


def run(code, stdin, lines=False):
    """Every line the program reaches, in order: [line, values, printed so far]; the last entry is the end (line None).
    With lines, calls count as their def line and a program that stops on an error or loops forever still gives
    the lines it reached."""
    result = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', TRACER], input=json.dumps([code, stdin, lines]).encode(),
                            capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    return json.loads(result.stdout)


# Put before the C++ program: each trace call prints \x02{"l": line, "v": {name: value}}\x03 to cout, so the
# steps and the program's own output stay in the order they happened.
CPP_HELPERS = r'''#include <iostream>
#include <string>
#include <type_traits>
#include <vector>
static bool algo_first_ = true;
static void algo_text_(const std::string &s) {
    std::cout << '"';
    for (char c : s) {
        if (c == '"' || c == '\\') std::cout << '\\';
        if (c == '\n') std::cout << "\\n"; else std::cout << c;
    }
    std::cout << '"';
}
static void algo_val_(bool x) { std::cout << (x ? "true" : "false"); }
static void algo_val_(char x) { algo_text_(std::string(1, x)); }
static void algo_val_(const std::string &x) { algo_text_(x); }
template <class T> static typename std::enable_if<std::is_arithmetic<T>::value>::type algo_val_(T x) { std::cout << x; }
template <class T> static void algo_val_(const std::vector<T> &v) {
    std::cout << '[';
    for (size_t i = 0; i < v.size(); i++) { if (i) std::cout << ','; algo_val_(v[i]); }
    std::cout << ']';
}
template <class T, size_t N> static void algo_val_(const T (&a)[N]) {
    std::cout << '[';
    for (size_t i = 0; i < N; i++) { if (i) std::cout << ','; algo_val_(a[i]); }
    std::cout << ']';
}
static int algo_count_ = 0;
static int algo_line_(int line) {
    if (++algo_count_ > %d) { std::cout << std::flush; std::_Exit(0); }
    std::cout << "\x02{\"l\":" << line << ",\"v\":{";
    algo_first_ = true;
    return 0;
}
template <class T> static int algo_put_(const char *name, const T &x) {
    if (!algo_first_) std::cout << ',';
    algo_first_ = false;
    algo_text_(name);
    std::cout << ':';
    algo_val_(x);
    return 0;
}
static int algo_end_() { std::cout << "}}\x03"; return 0; }
#include <cstdlib>
#line 1
''' % MAX_EVENTS
CPP_TYPE = r'(?:const\s+)?(?:unsigned\s+)?(?:long\s+long|long|int|short|bool|char|string|double|float|size_t|vector\s*<[^;]*?>)'


def code_only(line):
    """The line without strings, characters and a // comment, for counting braces and finding names."""
    line = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', line)
    return line.split('//')[0]


def split_top(text):
    """Split at commas that are not inside brackets, as in int lo = 1, hi = n;"""
    parts, depth, word = [], 0, ''
    for ch in text:
        depth += ch in '([{'
        depth -= ch in ')]}'
        if ch == ',' and depth == 0:
            parts.append(word)
            word = ''
        else:
            word += ch
    return parts + [word]


def watch(test, names):
    """What the steps need from an if line, worked out by C++ itself: the test, each [place], and both sides of ==."""
    found = [test] + re.findall(r'\w+\[([^\[\]]+)\]', test)
    sides = re.fullmatch(r'(.+?)\s*==\s*(.+)', test)
    return found + (list(sides.groups()) if sides else [])


def instrument(code):
    """The C++ program with a trace call before each statement of main, listing every variable in scope there."""
    lines = code.split('\n')
    start = next((i for i, l in enumerate(lines) if re.match(r'\s*int\s+main\s*\(', l)), None)
    assert start is not None, 'a C++ algorithm demo needs the whole program with int main()'
    out, scope, depth, previous = list(lines), [], 0, ''
    for i in range(start, len(lines)):
        text = code_only(lines[i]).strip()
        stripped = lines[i].strip()
        opening = depth
        if i > start and opening >= 1:
            braceless = re.match(r'(?:for|while|if)\b.*\)$|else$', previous)
            starts = stripped and not re.match(r'[{}#]|//|else\b|case\b|default\b', stripped) and (
                not previous or previous[-1] in ';{}' or braceless)
            if starts:
                names = [n for n, d, until in scope if until is None or until == i]
                ending = opening == 1 and re.match(r'return\b', stripped)
                calls = [f'algo_line_({-1 if ending else i + 1})'] + [f'algo_put_("{n}", {n})' for n in names]
                test = re.match(r'if\s*\((.*)\)\s*\{?$', text)
                if test and not ending:
                    calls += [f'algo_put_(R"algo({e.strip()})algo", ({e}))' for e in watch(test.group(1).strip(), names)]
                trace = ', '.join(calls + ['algo_end_()']) + '; '
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                out[i] = indent + ('{ ' + trace + stripped + ' }' if braceless else trace + stripped)
        # Names declared on this line are in scope from the next line; a for loop's own variable only inside it.
        declared = re.match(CPP_TYPE + r'\s+(.*);$', text)
        if declared and opening >= 1:
            for part in split_top(declared.group(1)):
                name = re.match(r'\s*(\w+)', part)
                if name:
                    scope.append((name.group(1), opening, None))
        loop = re.match(r'for\s*\(\s*' + CPP_TYPE + r'\s+(\w+)', text)
        depth += text.count('{') - text.count('}')
        if i > start and depth == 0:  # the closing brace of main: one last record, in case main has no return
            names = [n for n, d, u in scope if d <= 1]
            out[i] = ', '.join(['algo_line_(-1)'] + [f'algo_put_("{n}", {n})' for n in names] + ['algo_end_()']) + '; ' + lines[i]
            break
        if loop:  # a loop without braces owns only the next line
            scope.append((loop.group(1), opening + 1, None) if '{' in text else (loop.group(1), opening, i + 1))
        scope = [(n, d, u) for n, d, u in scope if d <= depth and (u is None or u >= i)]
        if text:
            previous = text
    return CPP_HELPERS + '\n'.join(out) + '\n'


def masked(line):
    """The line with the inside of strings and characters blanked and a // comment removed, same length."""
    out, quote, k = list(line), None, 0
    while k < len(line):
        ch = line[k]
        if quote:
            if ch == '\\':
                out[k] = ' '
                if k + 1 < len(line):
                    out[k + 1] = ' '
                k += 2
                continue
            if ch == quote:
                quote = None
            else:
                out[k] = ' '
        elif ch in '"\'':
            quote = ch
        elif line.startswith('//', k):
            return ''.join(out[:k]) + ' ' * (len(line) - k)
        k += 1
    return ''.join(out)


def closing(text, start):
    """The index of the bracket that closes the one at start."""
    depth = 0
    for k in range(start, len(text)):
        depth += text[k] == '('
        depth -= text[k] == ')'
        if depth == 0:
            return k
    return -1


def instrument_lines(code):
    """For a trace page: a record of each line as it runs, in every function, and of each check of a loop.

    Records go before each statement, into the test of for, while and else if (so a loop line is recorded each
    time it is checked, like Python), and right after a function's { (a call reaches its header line)."""
    lines = code.split('\n')
    out, depth, previous, header, inside = list(lines), 0, '', None, False
    record = lambda n: f'algo_line_({n}), algo_end_()'
    for i, line in enumerate(lines):
        text = masked(line)
        bare = text.strip()
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        opening = depth
        if opening == 0 and re.match(r'(?!(?:if|for|while|switch|return|else)\b)[\w:<>,*&\s]+?\b\w+\s*\([^;]*\)\s*(?:const\s*)?\{?$', bare) \
                and not bare.startswith(('#', 'using', 'typedef', 'struct', 'class')):
            header = i
        if header is not None and '{' in bare and opening == 0:
            k = text.index('{')
            out[i] = line[:k + 1] + ' ' + record(header + 1) + '; ' + line[k + 1:]
            header, inside = None, True
        elif inside and opening >= 1 and stripped:  # only in function bodies, not in a struct or an array's { }
            loop = re.match(r'(for|while)\s*\(', bare)
            elif_ = re.match(r'\}\s*else\s+if\s*\(', bare)
            braceless = re.match(r'(?:for|while|if)\b.*\)$|(?:\}\s*)?else$', previous)
            if loop or elif_:
                start = text.index('(', text.index(loop.group(1) if loop else 'if'))
                end = closing(text, start)
                inside = line[start + 1:end]
                parts = [k for k, ch in enumerate(masked(inside)) if ch == ';'] if loop and loop.group(1) == 'for' else []
                if len(parts) == 2:
                    test = inside[parts[0] + 1:parts[1]].strip() or 'true'
                    inside = inside[:parts[0] + 1] + f' ({record(i + 1)}, ({test}));' + inside[parts[1] + 1:]
                    out[i] = line[:start + 1] + inside + line[end:]
                elif loop and loop.group(1) == 'for':  # for (x : list): recorded at the top of each pass
                    if bare.endswith('{'):
                        out[i] = line.rstrip() + ' ' + record(i + 1) + ';'
                else:
                    out[i] = line[:start + 1] + f'({record(i + 1)}, ({inside}))' + line[end:]
            elif not re.match(r'[{}#]|//|else\b|case\b|default\b', stripped) and (
                    not previous or previous[-1] in ';{}' or braceless):
                body = record(i + 1) + '; ' + stripped
                out[i] = indent + ('{ ' + body + ' }' if braceless else body)
        depth += bare.count('{') - bare.count('}')
        if depth == 0:
            inside = False
        if bare:
            previous = bare
    return CPP_HELPERS + '\n'.join(out) + '\n'


def line_runs(code, stdin, language):
    """The lines a program reaches, in order, with the simple values in scope before each (Python only).

    For trace pages: the run goes on through an error or an endless loop, and C++ records every function."""
    if language == 'python':
        events = run(code, stdin, lines=True)
        return [(e[0], e[1]) for e in events if e[0] is not None]
    with tempfile.TemporaryDirectory() as folder:
        exe = Path(folder) / ('trace.exe' if os.name == 'nt' else 'trace')
        built = subprocess.run([compiler(), '-std=c++11', '-Wno-error=parentheses', '-x', 'c++', '-', '-o', str(exe)], input=instrument_lines(code).encode(),
                               capture_output=True, timeout=60)
        assert built.returncode == 0, 'the traced C++ program does not compile:\n' + built.stderr.decode(errors='replace')
        try:
            result = subprocess.run([str(exe)], input=stdin.encode(), capture_output=True, timeout=10)
            text = result.stdout.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired as late:
            text = (late.stdout or b'').decode('utf-8', errors='replace')
    found = []
    for piece in text.split('\x02')[1:]:
        if '\x03' in piece:
            found.append((json.loads(piece.split('\x03', 1)[0])['l'], {}))
    return found


def compiler():
    found = os.environ.get('CXX') or shutil.which('clang++') or shutil.which('g++')
    assert found, 'No C++ compiler found for the algorithm demo'
    return found


def run_cpp(code, stdin):
    """Compile the traced copy, run it, and read its trace calls back as events."""
    with tempfile.TemporaryDirectory() as folder:
        exe = Path(folder) / ('demo.exe' if os.name == 'nt' else 'demo')
        built = subprocess.run([compiler(), '-std=c++11', '-Wno-error=parentheses', '-x', 'c++', '-', '-o', str(exe)], input=instrument(code).encode(),
                               capture_output=True, timeout=60)
        assert built.returncode == 0, 'the traced C++ program does not compile:\n' + built.stderr.decode(errors='replace')
        result = subprocess.run([str(exe)], input=stdin.encode(), capture_output=True, timeout=10)
    assert result.returncode == 0, 'the C++ program of the demo did not finish normally'
    text = result.stdout.decode('utf-8', errors='replace').replace('\r\n', '\n')
    events, out = [], ''
    for k, piece in enumerate(text.split('\x02')):
        if k:
            record, piece = piece.split('\x03', 1)
            record = json.loads(record)
            events.append([None if record['l'] < 0 else record['l'], record['v'], out])
        out += piece
    assert len(events) <= MAX_EVENTS, 'too many steps'
    if not events or events[-1][0] is not None:
        events.append([None, events[-1][1] if events else {}, out])
    events[-1][2] = out
    return events


def condition(source):
    """The test of an if line: Python if x: or elif x:, C++ if (x) {."""
    match = re.fullmatch(r'\s*(?:if|elif)\s+(.*):\s*', source) or re.fullmatch(r'\s*if\s*\((.*)\)\s*\{?\s*', code_only(source))
    return match and match.group(1).strip()


def value(expr, names):
    """C++ worked its own expressions out and recorded them; Python ones are worked out here."""
    if expr in names:
        return names[expr]
    return eval(expr, {'__builtins__': {}}, dict(names))


def steps(kind, code, stdin, names, language='python'):
    """The run as player steps. names maps a role to the variable on the page, such as {"list": "a"}."""
    assert kind in KINDS, f'data-algo must be one of {", ".join(KINDS)}'
    assert language in ('python', 'cpp'), f'algorithm demos trace Python and C++, not {language}'
    lines = code.split('\n')
    events = run(code, stdin) if language == 'python' else run_cpp(code, stdin)
    if names.get('size'):  # only the used part of a C++ array
        for event in events:
            if names['list'] in event[1] and isinstance(event[1].get(names['size']), int):
                event[1][names['list']] = event[1][names['list']][:event[1][names['size']]]
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
    steps, settled = [], None
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
                settled = now[name]
            steps.append(dict(type='compare', line=line, list=now[name], at=spots, op=op.group(1),
                              swap=bool(value(test, now)), out=before[2]))
        elif steps and name in new and new[name] != now[name]:
            if sorted(new[name]) != sorted(settled):
                continue  # halfway through a swap by way of a temporary variable
            changed = [i for i, (x, y) in enumerate(zip(settled, new[name])) if x != y]
            assert len(changed) == 2, f'a sort demo can only swap two places at a time (line {line})'
            steps.append(dict(type='swap', line=line, list=new[name], at=changed, out=after[2]))
            settled = new[name]
        elif steps and printed(before, after):
            if steps[-1]['type'] == 'print':  # a loop that prints the numbers one by one is one step
                steps[-1].update(text=steps[-1]['text'] + printed(before, after), out=after[2])
            else:
                steps.append(dict(type='print', line=line, list=settled, text=printed(before, after), out=after[2]))
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
        self.demos, self.lines, self.code, self.full, self.first = [], None, None, None, 1
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
            roles.update({role: attrs[f'data-{role}'] for role in OPTIONAL[kind] if attrs.get(f'data-{role}')})
            self.demos.append(dict(kind=kind, names=roles, stdin=attrs.get('data-stdin') or '', trace=attrs.get('data-trace')))
        if tag == 'pre' and 'code' in classes and 'was' not in classes and self.code is None:
            self.code = self.lines = []
            # A page that shows only some lines of a longer program runs the whole one (data-full, from data-file).
            if attrs.get('data-full') is not None:
                self.full = attrs['data-full']
                self.first = int((attrs.get('data-lines') or '1').split('-')[0])
        if self.lines is not None and tag == 'span' and 'ln' in classes:
            self.lines.append('')

    def handle_data(self, data):
        if self.lines:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.lines = None


    def program(self):
        """The program the demo runs, and the line of it the page's first code line is."""
        return (self.full if self.full is not None else '\n'.join(self.code or [])).rstrip('\n'), self.first


def demos(section, language='python'):
    """Each demo of a page with its steps: the program is the one in the page's code editor, run for real."""
    found = Demos(section)
    assert not found.demos or found.code, 'an algorithm demo needs its program in a pre.code on the same page'
    code, first = found.program()
    for demo in found.demos:
        names = dict(demo['names'])
        demo['code'] = code
        demo['data'] = dict(kind=demo['kind'], names=names, first=first, language=language,
                            steps=steps(demo['kind'], code, demo['stdin'], names, language))
    return found.demos


def encode(data):
    return html.escape(json.dumps(data, ensure_ascii=False, separators=(',', ':')), quote=True)


def embed(slides, language='python'):
    """Write the steps into the div.algo of every built page, as data-trace."""
    def page(match):
        section = match.group(0)
        if 'class="algo"' not in section:
            return section
        found = demos(section, language)
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
