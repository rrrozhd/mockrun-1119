import os
import subprocess
import sys
import tempfile
import unittest

from mdtable.cli import format_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MESSY = b"# Title\n\n|a|b|\n|-|-:|\n|long cell|1|\n\nafter\n"
TIDY = (
    b"# Title\n\n"
    b"| a         |    b |\n"
    b"| --------- | ---: |\n"
    b"| long cell |    1 |\n"
    b"\nafter\n"
)


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "mdtable", *args],
        input=stdin,
        capture_output=True,
        cwd=ROOT,
    )


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

    def write(self, data):
        path = os.path.join(self.directory, "doc.md")
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_file_argument_writes_formatted_markdown(self):
        result = run(self.write(MESSY))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, TIDY)

    def test_stdin_writes_formatted_markdown(self):
        result = run(stdin=MESSY)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, TIDY)

    def test_check_passes_on_formatted_input(self):
        result = run("--check", self.write(TIDY))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")

    def test_check_fails_on_unformatted_input(self):
        result = run("--check", self.write(MESSY))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"not formatted", result.stderr)

    def test_check_reads_stdin(self):
        self.assertEqual(run("--check", stdin=MESSY).returncode, 1)
        self.assertEqual(run("--check", stdin=TIDY).returncode, 0)

    def test_missing_file_exits_2(self):
        result = run(os.path.join(self.directory, "absent.md"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"mdtable:", result.stderr)

    def test_invalid_utf8_exits_2(self):
        result = run(stdin=b"\xff\xfe|a|\n")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")

    def test_crlf_without_final_newline_is_kept(self):
        messy = b"intro  \r\n\r\n|a|b|\r\n|-|-|\r\n|1|2|\r\n\r\ntail\twith tab"
        result = run(stdin=messy)
        self.assertEqual(
            result.stdout,
            b"intro  \r\n\r\n"
            b"| a   | b   |\r\n| --- | --- |\r\n| 1   | 2   |\r\n"
            b"\r\ntail\twith tab",
        )

    def test_table_as_last_line_without_newline(self):
        result = run(stdin=b"|a|b|\n|-|-|\n|1|2|")
        self.assertEqual(result.stdout, b"| a   | b   |\n| --- | --- |\n| 1   | 2   |")

    def test_table_in_fenced_block_is_untouched(self):
        fenced = b"```\n|a|b|\n|-|-|\n|1|2|\n```\n"
        self.assertEqual(run(stdin=fenced).stdout, fenced)

    def test_document_without_tables_is_untouched(self):
        plain = b"no | table here\r\njust text\n\n\n"
        self.assertEqual(run(stdin=plain).stdout, plain)

    def test_empty_input(self):
        result = run(stdin=b"")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")


class FormatTextTest(unittest.TestCase):
    def test_formatting_twice_changes_nothing(self):
        once = format_text(MESSY.decode())
        self.assertEqual(format_text(once), once)

    def test_indented_table_keeps_its_indent(self):
        text = "- item\n\n  |a|b|\n  |-|-|\n  |1|2|\n"
        self.assertEqual(
            format_text(text),
            "- item\n\n  | a   | b   |\n  | --- | --- |\n  | 1   | 2   |\n",
        )

    def test_mixed_line_endings_are_kept(self):
        text = "one\r\ntwo\nthree\r\n"
        self.assertEqual(format_text(text), text)


if __name__ == "__main__":
    unittest.main()
