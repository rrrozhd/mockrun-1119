"""Format the lines of one Markdown pipe table."""

import re


def _split_row(line: str) -> list[str]:
    line = line.strip(" \t")
    cells = []
    start = 0
    # Consume backslash escapes as pairs so only unescaped pipes split cells.
    for token in re.finditer(r"\\.|[|]", line):
        if token[0] == "|":
            if token.start() > 0:
                cells.append(line[start:token.start()].strip(" \t"))
            start = token.end()
    if start < len(line):
        cells.append(line[start:].strip(" \t"))
    return cells


def _pad(cell: str, width: int, marker: str) -> str:
    if marker.endswith(":"):
        if marker.startswith(":"):
            left = (width - len(cell)) // 2
            return (" " * left + cell).ljust(width)
        return cell.rjust(width)
    return cell.ljust(width)


def format_table(lines: list[str]) -> list[str]:
    """Align a header, delimiter row, and optional body, without line endings."""
    rows = [_split_row(line) for line in lines]
    markers = rows[1]
    column_count = max(map(len, rows))
    markers.extend(["---"] * (column_count - len(markers)))
    data = [rows[0], *rows[2:]]
    for row in data:
        row.extend([""] * (column_count - len(row)))

    for column, marker in enumerate(markers):
        left = ":" if marker.startswith(":") else ""
        right = ":" if marker.endswith(":") else ""
        min_width = 3 + len(left) + len(right)
        width = max(min_width, max(len(row[column]) for row in data))
        markers[column] = left + "-" * (width - len(left) - len(right)) + right
        for row in data:
            row[column] = _pad(row[column], width, marker)

    return ["| " + " | ".join(row) + " |" for row in rows]
