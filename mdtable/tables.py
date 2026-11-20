"""Find pipe tables in Markdown lines (line endings already removed)."""

import re

# A backslash escapes the next character, so pairs are consumed and only unescaped pipes match.
_TOKEN = re.compile(r"\\.|\|")
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
_ALIGN_CELL = re.compile(r"\s*:?-+:?\s*")


def _pipes(line):
    """Positions of the unescaped pipes in a line."""
    return [m.start() for m in _TOKEN.finditer(line) if m.group() == "|"]


def split_cells(line):
    """Split a row on unescaped pipes, dropping the empty text outside the outer pipes."""
    line = line.strip()
    bounds = [-1] + _pipes(line) + [len(line)]
    cells = [line[a + 1:b] for a, b in zip(bounds, bounds[1:])]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _is_row(line):
    """A line that can open a table: an unescaped pipe and not indented code."""
    indent = len(line) - len(line.lstrip(" "))
    return indent < 4 and not line.startswith("\t") and bool(_pipes(line))


def _is_align_row(line):
    cells = split_cells(line)
    return _is_row(line) and bool(cells) and all(_ALIGN_CELL.fullmatch(c) for c in cells)


def _closes(fence, line):
    m = _FENCE.match(line)
    return bool(
        m
        and m.group(1)[0] == fence[0]
        and len(m.group(1)) >= len(fence)
        and not line[m.end():].strip()
    )


def find_tables(lines):
    """Return the half-open (start, end) line ranges of every pipe table.

    A table is a header row followed by an alignment row with the same number of
    cells, then every following line that is not blank, has an unescaped pipe, is
    not indented four or more spaces and does not open a fence. Lines inside
    fenced code blocks are never part of a table.
    """
    tables = []
    fence = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if fence:
            if _closes(fence, line):
                fence = None
            i += 1
            continue
        m = _FENCE.match(line)
        if m:
            fence = m.group(1)
            i += 1
            continue
        if (
            i + 1 < len(lines)
            and _is_row(line)
            and _is_align_row(lines[i + 1])
            and len(split_cells(line)) == len(split_cells(lines[i + 1]))
        ):
            end = i + 2
            while (
                end < len(lines)
                and lines[end].strip()
                and _is_row(lines[end])
                and not _FENCE.match(lines[end])
            ):
                end += 1
            tables.append((i, end))
            i = end
            continue
        i += 1
    return tables
