"""Command line: read Markdown, line up its pipe tables, write it back."""

import argparse
import os
import shutil
import sys
import tempfile

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


def _replace(path, data):
    """Give path new contents without ever leaving half a file behind."""
    target = os.path.realpath(path)  # rewrite a symlink's target, keep the link
    if os.stat(target).st_nlink > 1:
        # A rename would leave the file's other names on the old contents.
        raise OSError(0, "has other hard links, not rewritten")
    descriptor, temporary = tempfile.mkstemp(
        dir=os.path.dirname(target), prefix=".mdtable-"
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
        shutil.copymode(target, temporary)
        os.replace(temporary, target)
    except BaseException:
        os.unlink(temporary)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mdtable",
        description="Line up the columns of Markdown pipe tables.",
    )
    parser.add_argument(
        "files", nargs="*", metavar="FILE", help="Markdown file (default: stdin)"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if any input is not formatted",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="rewrite each FILE in place and print the ones that changed",
    )
    args = parser.parse_args(argv)
    if args.write and not args.files:
        parser.error("--write needs at least one FILE")
    if len(args.files) > 1 and not (args.check or args.write):
        parser.error("several files need --check or --write")

    status = 0
    for path in args.files or [None]:
        name = path or "stdin"
        try:
            if path is None:
                data = sys.stdin.buffer.read()
            else:
                with open(path, "rb") as handle:
                    data = handle.read()
            # Bytes in and out: text mode would rewrite line endings.
            text = data.decode("utf-8")
            result = format_text(text)
            if args.check:
                if result != text:
                    print(f"mdtable: {name} is not formatted", file=sys.stderr)
                    status = max(status, 1)
            elif args.write:
                if result != text:
                    _replace(path, result.encode("utf-8"))
                    # Bytes, so a name the terminal's encoding lacks still prints.
                    sys.stdout.buffer.write(os.fsencode(path) + b"\n")
            else:
                sys.stdout.buffer.write(result.encode("utf-8"))
        except UnicodeDecodeError:
            print(f"mdtable: {name}: not valid UTF-8", file=sys.stderr)
            status = 2
        except OSError as error:
            print(f"mdtable: {name}: {error.strerror}", file=sys.stderr)
            status = 2
    return status
