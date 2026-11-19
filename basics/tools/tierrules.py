"""Size tiers that pages name with a class instead of writing a font-size, and how much text each holds. build/check.py and
PROMPT.md ("档位") follow this. Widths are in em of the code font as the browser draws it: a Chinese character (or other
wide one) is 1, any other character 0.6."""
import html
import re

# Notes (.slip): the class, its font size, and the longest line it holds in a 600px note (520px for the text).
SLIP = [('short', 72), ('', 56), ('long', 44), ('longest', 34)]
TEXT_WIDTH = 520
# While lessons move to tiers, a note or box that still sets its own font-size is passed over; True once all have moved.
STRICT = False


def width(line):
    return sum(1 if ord(ch) > 0x2e7f else 0.6 for ch in line)


def room(size, text=TEXT_WIDTH):
    return text / size


def slip_text_width(start, row=0):
    """How wide a note's text can be: from its own width when it has one, else from how many notes share its row
    (.notes in lay-notes), else the 600px note."""
    own = re.search(r'width:\s*(\d+)px', start)
    if own:
        return int(own.group(1)) - 80
    if row:
        return (1752 - 34 * (row - 1)) // row - 104
    return TEXT_WIDTH


def slip_lines(body):
    """The lines of text in a note (its pre blocks), without tags."""
    return [l for pre in re.findall(r'<pre[^>]*>(.*?)</pre>', body, re.S)
            for l in html.unescape(re.sub(r'<[^>]+>', '', pre)).split('\n')]


def slip_widest(body):
    return max(map(width, slip_lines(body)), default=0)


TEXT_HEIGHT = 640  # the lines of one note, all its pre blocks together, at line-height 1.4


def slip_fits(body, size, text=TEXT_WIDTH):
    lines = slip_lines(body)
    return max(map(width, lines), default=0) <= room(size, text) and len(lines) * size * 1.4 <= TEXT_HEIGHT


def slip_tier(body, text=TEXT_WIDTH):
    """The tier for a note's text: the biggest it fits, by its longest line and by how many lines it has; the last tier
    wraps long lines."""
    return next((name for name, size in SLIP[:-1] if slip_fits(body, size, text)), SLIP[-1][0])


def slips(section):
    """Each note on a page: (its start tag, its body, the width its text can take)."""
    out = []
    notes = re.search(r'<div class="notes">(.*?)\n  </div>', section, re.S)
    row = len(re.findall(r'<div class="slip\b', notes.group(1))) if notes else 0
    for m in re.finditer(r'(<div class="slip\b[^"]*"[^>]*>)(.*?)</div>', section, re.S):
        inside = notes and notes.start(1) <= m.start() < notes.end(1)
        out.append((m, slip_text_width(m.group(1), row if inside else 0)))
    return out


def slip_named(classes):
    names = [name for name, _ in SLIP if name and name in classes]
    return names[0] if names else ''


# Variable boxes (.box in a walk page's right column): the class and the font size of the value (b). The value's room is
# the column less the label column (as wide as the widest label, at least 130px) and the 30px gap.
BOX = [('', 120), ('long', 84), ('longer', 60), ('longest', 40)]
STACKED = 230  # a box whose label sits above its value (display:block): the most its value's lines may take
COLUMN = {'': 614, 'wide': 514, 'narrow': 734}


def box_room(section):
    head = section.split('\n')[0]
    column = COLUMN['wide' if ' wide' in head else 'narrow' if ' narrow' in head else '']
    labels = []
    for m in re.finditer(r'<div class="box([^"]*)"[^>]*>\s*<i[^>]*>(.*?)</i>', section, re.S):
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))
        labels.append(width(text) * (40 if 'out' in m.group(1).split() else 44))
    return column - max([130] + labels) - 30


def box_value(body):
    b = re.search(r'<b[^>]*>(.*?)</b>', body, re.S)
    lines = re.split(r'<br\s*/?>', b.group(1)) if b else ['']
    return max(width(html.unescape(re.sub(r'<[^>]+>', '', l))) for l in lines)


def box_lines(body):
    b = re.search(r'<b[^>]*>(.*?)</b>', body, re.S)
    return len(re.split(r'<br\s*/?>', b.group(1))) if b else 1


def box_fits(start, body, size, room):
    """A value fits beside its label; a stacked box (label above, display:block) has the column's width but only so
    much height for its lines."""
    if 'display:block' in start:
        return box_value(body) * size <= room + 160 and box_lines(body) * size * 1.3 <= STACKED
    return box_value(body) * size <= room


def box_tier(body, room, start=''):
    return next((name for name, size in BOX[:-1] if box_fits(start, body, size, room)), BOX[-1][0])


def box_named(classes):
    names = [name for name, _ in BOX if name and name in classes]
    return names[0] if names else ''


def check_section(section, where):
    """Each note and variable box on a page uses a tier its text fits, and not one two steps bigger than it needs.
    Returns how many it checked. A note in a row (.notes) may be a step or two bigger than its own text needs: the row
    shares one size."""
    checked = 0
    order = [n for n, _ in SLIP]
    for m, text in slips(section):
        start, body = m.group(1), m.group(2)
        if not STRICT and 'font-size' in body:
            continue
        assert not re.search(r'<pre style="[^"]*font(-size)?:[^;"]*\d+px', body), \
            f'{where}: a note sets its own font-size; name a tier instead (PROMPT.md "档位")'
        tier = slip_named(re.search(r'class="([^"]*)"', start).group(1).split())
        size = dict(SLIP)[tier]
        widest, lines = slip_widest(body), len(slip_lines(body))
        assert tier == SLIP[-1][0] or slip_fits(body, size, text), \
            f'{where}: the note "{slip_lines(body)[0][:12]}" does not fit tier {tier or "regular"} ' \
            f'(longest line {widest:.1f} wide, {lines} lines; room {room(size, text):.1f}); use a smaller tier'
        better = order.index(tier) - 2
        in_row = text != TEXT_WIDTH and 'width:' not in start
        assert better < 0 or in_row or not slip_fits(body, SLIP[better][1], text), \
            f'{where}: the note "{slip_lines(body)[0][:12]}" fits tier {SLIP[better][0] or "regular"}; use a bigger tier'
        checked += 1
    if 'lay-walk' in section.split('\n')[0] and '<div class="box' in section:
        space = box_room(section)
        boxes = list(re.finditer(r'<div class="box\b([^"]*)"[^>]*>(.*?)</div>', section, re.S))
        legacy = not any(box_named(m.group(1).split()) for m in boxes) and (
            '<i style=' in section or re.search(r'<b style="[^"]*font(-size)?:[^;"]*\d+px', section))
        if not STRICT and legacy:
            return checked
        for m in boxes:
            assert not re.search(r'<b style="[^"]*font(-size)?:[^;"]*\d+px', m.group(2)), \
                f'{where}: a variable box sets its own font-size; name a tier instead (PROMPT.md "档位")'
            tier = box_named(m.group(1).split())
            assert tier == BOX[-1][0] or box_fits(m.group(0), m.group(2), dict(BOX)[tier], space), \
                f'{where}: a variable box value does not fit tier {tier or "regular"}; use a smaller tier for every box on the page'
            checked += 1
    return checked
