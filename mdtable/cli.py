"""Command line: read Markdown, line up its pipe tables, write it back."""

import argparse
import sys

from .format import format_table
from .tables import find_tables


def format_text(text):
    """Return text with every pipe table formatted and all else untouched."""
    parts = text.split("\n")
    # Each line keeps its own ending ("\n", "\r\n" or none) so it can be put back.
    bodies = [part[:-1] if part.endswith("\r") else part for part in parts]
    endings = [part[len(body):] + "\n" for part, body in zip(parts, bodies)]
    endings[-1] = endings[-1][:-1]  # nothing follows the last newline
    for start, end in find_tables(bodies):
        # format_table drops leading spaces; put the header's back so a table
        # nested under a list item stays in it.
        header = bodies[start]
        indent = header[: len(header) - len(header.lstrip(" "))]
        rows = format_table(bodies[start:end])
        bodies[start:end] = [indent + row for row in rows]
    return "".join(body + ending for body, ending in zip(bodies, endings))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mdtable",
        description="Line up the columns of Markdown pipe tables.",
    )
    parser.add_argument("file", nargs="?", help="Markdown file (default: stdin)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if the input is not formatted",
    )
    args = parser.parse_args(argv)

    try:
        if args.file is None:
            data = sys.stdin.buffer.read()
        else:
            with open(args.file, "rb") as handle:
                data = handle.read()
        # Bytes in and out: text mode would rewrite line endings.
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"mdtable: {error}", file=sys.stderr)
        return 2

    result = format_text(text)
    if args.check:
        if result == text:
            return 0
        print(f"mdtable: {args.file or 'stdin'} is not formatted", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(result.encode("utf-8"))
    return 0
