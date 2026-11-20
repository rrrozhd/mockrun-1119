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


def run(*args, stdin=None, env=None):
    return subprocess.run(
        [sys.executable, "-m", "mdtable", *args],
        input=stdin,
        capture_output=True,
        cwd=ROOT,
        env=env,
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


class SeveralFilesTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

    def path(self, name):
        return os.path.join(self.directory, name)

    def write(self, name, data):
        with open(self.path(name), "wb") as handle:
            handle.write(data)
        return self.path(name)

    def read(self, name):
        with open(self.path(name), "rb") as handle:
            return handle.read()

    def test_write_rewrites_only_files_that_change(self):
        messy = self.write("messy.md", MESSY)
        tidy = self.write("tidy.md", TIDY)
        os.utime(tidy, (1_000_000_000, 1_000_000_000))
        result = run("--write", messy, tidy)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode().splitlines(), [messy])
        self.assertEqual(self.read("messy.md"), TIDY)
        self.assertEqual(self.read("tidy.md"), TIDY)
        self.assertEqual(os.stat(tidy).st_mtime, 1_000_000_000)
        self.assertEqual(sorted(os.listdir(self.directory)), ["messy.md", "tidy.md"])

    def test_second_write_changes_nothing(self):
        messy = self.write("messy.md", MESSY)
        run("--write", messy)
        result = run("--write", messy)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(self.read("messy.md"), TIDY)

    def test_write_keeps_crlf_and_missing_final_newline(self):
        path = self.write("crlf.md", b"x\r\n\r\n|a|b|\r\n|-|-|\r\n\r\nend")
        run("--write", path)
        self.assertEqual(
            self.read("crlf.md"),
            b"x\r\n\r\n| a   | b   |\r\n| --- | --- |\r\n\r\nend",
        )

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_write_keeps_permission_bits(self):
        messy = self.write("messy.md", MESSY)
        os.chmod(messy, 0o640)
        run("--write", messy)
        self.assertEqual(os.stat(messy).st_mode & 0o777, 0o640)

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_write_follows_a_symlink(self):
        self.write("real.md", MESSY)
        link = self.path("link.md")
        os.symlink("real.md", link)
        result = run("--write", link)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.islink(link))
        self.assertEqual(self.read("real.md"), TIDY)

    @unittest.skipIf(os.name == "nt", "hard links differ on Windows")
    def test_write_refuses_a_file_with_other_hard_links(self):
        messy = self.write("messy.md", MESSY)
        os.link(messy, self.path("twin.md"))
        result = run("--write", messy)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"hard links", result.stderr)
        self.assertEqual(self.read("messy.md"), MESSY)
        self.assertEqual(self.read("twin.md"), MESSY)

    @unittest.skipIf(
        os.name == "nt" or os.geteuid() == 0, "needs a folder that refuses writes"
    )
    def test_failed_write_keeps_the_original(self):
        messy = self.write("messy.md", MESSY)
        os.chmod(self.directory, 0o555)
        self.addCleanup(os.chmod, self.directory, 0o755)
        result = run("--write", messy)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"messy.md", result.stderr)
        self.assertEqual(self.read("messy.md"), MESSY)
        self.assertEqual(os.listdir(self.directory), ["messy.md"])

    def test_write_reports_names_the_output_encoding_lacks(self):
        accented = self.write("caf\u00e9.md", MESSY)
        plain = self.write("next.md", MESSY)
        result = run(
            "--write", accented, plain, env={**os.environ, "PYTHONIOENCODING": "ascii"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(), [os.fsencode(accented), os.fsencode(plain)]
        )
        self.assertEqual(self.read("caf\u00e9.md"), TIDY)
        self.assertEqual(self.read("next.md"), TIDY)

    def test_write_carries_on_after_a_bad_file(self):
        messy = self.write("messy.md", MESSY)
        binary = self.write("binary.md", b"\xff\xfe|a|\n")
        result = run("--write", self.path("absent.md"), binary, messy)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"absent.md", result.stderr)
        self.assertIn(b"binary.md: not valid UTF-8", result.stderr)
        self.assertEqual(self.read("messy.md"), TIDY)
        self.assertEqual(self.read("binary.md"), b"\xff\xfe|a|\n")

    def test_check_names_every_unformatted_file(self):
        one = self.write("one.md", MESSY)
        two = self.write("two.md", MESSY)
        tidy = self.write("tidy.md", TIDY)
        result = run("--check", one, tidy, two)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"one.md is not formatted", result.stderr)
        self.assertIn(b"two.md is not formatted", result.stderr)
        self.assertNotIn(b"tidy.md", result.stderr)
        self.assertEqual(self.read("one.md"), MESSY)

    def test_check_reports_a_bad_file_over_an_unformatted_one(self):
        messy = self.write("messy.md", MESSY)
        result = run("--check", messy, self.path("absent.md"))
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"messy.md is not formatted", result.stderr)

    def test_usage_errors_write_nothing(self):
        messy = self.write("messy.md", MESSY)
        other = self.write("other.md", MESSY)
        for arguments in (
            ["--write", "--check", messy],
            ["--write"],
            [messy, other],
        ):
            with self.subTest(arguments=arguments):
                result = run(*arguments, stdin=b"")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
        self.assertEqual(self.read("messy.md"), MESSY)
        self.assertEqual(self.read("other.md"), MESSY)


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
