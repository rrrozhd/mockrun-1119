# mdtable

`mdtable` lines up the columns of Markdown pipe tables. It pads every cell to
its column's width, keeps and obeys the alignment row (`:---` left, `:---:`
centre, `---:` right), and leaves everything outside a table exactly as it
was, including line endings and tables inside fenced code blocks.

It needs only Python 3 and its standard library; there is nothing to install.

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

Check whether a file is already formatted, without writing anything:

```sh
python3 -m mdtable --check notes.md
```

| Exit code | Meaning                                                 |
| --------- | ------------------------------------------------------- |
| 0         | formatted output written, or `--check` found no changes |
| 1         | `--check` found a table that is not formatted           |
| 2         | the file could not be read or is not valid UTF-8        |

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

## Limits

- Width is counted in code points, so wide characters such as CJK text or
  emoji may not line up.
- There is no in-place mode: redirect the output to a new file.

## Tests

```sh
python3 -m unittest
```

The tests also run every example above through the formatter and compare the
result with its "After" block.
