# mdtable

`mdtable` lines up the columns of Markdown pipe tables. It pads every cell to
its column's width, keeps and obeys the alignment row (`:---` left, `:---:`
centre, `---:` right), and leaves everything outside a table exactly as it
was, including line endings and tables inside fenced code blocks.

## Requirements

Python 3.9 or newer, and only its standard library; there is nothing to
install.

## Usage

Run it from the repository's root.

Format a file and write the result to stdout:

```sh
python3 -m mdtable notes.md
```

Read from stdin instead:

```sh
python3 -m mdtable < notes.md
```

Check whether files are already formatted, without writing anything:

```sh
python3 -m mdtable --check notes.md docs/*.md
```

Print the version:

```sh
python3 -m mdtable --version
```

Format files in place:

```sh
python3 -m mdtable --write notes.md docs/*.md
```

`--write` rewrites only the files that change and prints their paths. Each one
is written to a temporary file and then renamed over the original, so an
interrupted run cannot leave half a file. Permission bits are kept, and a
symlink's target is rewritten rather than the link. A file that has other hard
links is reported and left alone, because a rename would leave its other names
on the old contents.

More than one file needs `--check` or `--write`. A file that cannot be read is
reported and skipped, and the others are still handled.

| Exit code | Meaning                                                                                                                  |
| --------- | ------------------------------------------------------------------------------------------------------------------------ |
| 0         | output written, nothing to change, or `--write` finished                                                                 |
| 1         | `--check` found a table that is not formatted, and no file failed                                                        |
| 2         | wrong usage, or any file failed: it could not be read, is not valid UTF-8, could not be written, or has other hard links |

Exit code 2 wins: a `--check` run that finds an unformatted file and also
fails on another file exits 2.

## Examples

Each column follows its alignment marker.

Before:

```markdown
| Fruit | Price | Stock |
|:--|:-:|--:|
| Apple | 1.20 | 14 |
| Watermelon | 3.5 | 2 |
```

After:

```markdown
| Fruit      | Price | Stock |
| :--------- | :---: | ----: |
| Apple      | 1.20  |    14 |
| Watermelon |  3.5  |     2 |
```

An escaped pipe stays inside its cell, and a short row gains empty cells.

Before:

```markdown
| Command | What it does |
|---|---|
| `mdtable FILE` | format a file |
| `a \| b` | an escaped pipe stays in its cell |
| short |
```

After:

```markdown
| Command        | What it does                      |
| -------------- | --------------------------------- |
| `mdtable FILE` | format a file                     |
| `a \| b`       | an escaped pipe stays in its cell |
| short          |                                   |
```

Cells are padded by the width they take in a monospace terminal, not by their
number of characters, so CJK text and emoji line up. East Asian wide and
fullwidth characters count as two columns; combining marks and invisible
format characters (zero-width joiners, variation selectors) count as none.

Before:

```markdown
| City | Population |
|---|--:|
| 東京 | 14 million |
| Paris 🗼 | 2 million |
```

After:

```markdown
| City     | Population |
| -------- | ---------: |
| 東京     | 14 million |
| Paris 🗼 |  2 million |
```

## Limits

- Display width follows Unicode's East Asian Width property, as most
  terminals do. A character Unicode does not mark as wide (such as `❤`, even
  followed by an emoji variation selector) counts as one column, and an emoji sequence joined with zero-width joiners counts as
  each of its parts, so a terminal that draws these differently may not line
  them up.
- A table inside a block quote (lines starting with `>`) is left as it is,
  and `--check` does not report it.

## Tests

```sh
python3 -m unittest
```

The tests also run every example above through the formatter and compare the
result with its "After" block.
