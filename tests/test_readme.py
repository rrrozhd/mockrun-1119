import os
import re
import unittest

from mdtable.cli import format_text

README = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")

EXAMPLE = re.compile(
    r"Before:\n\n```markdown\n(.*?)```\n\nAfter:\n\n```markdown\n(.*?)```",
    re.DOTALL,
)


def read_readme():
    with open(README, encoding="utf-8", newline="") as handle:
        return handle.read()


class ReadmeTest(unittest.TestCase):
    def test_examples_show_real_output(self):
        examples = EXAMPLE.findall(read_readme())
        self.assertGreaterEqual(len(examples), 2, "README examples not found")
        for before, after in examples:
            with self.subTest(before=before):
                self.assertEqual(format_text(before), after)

    def test_readme_states_python_requirement(self):
        self.assertIn("## Requirements\n\nPython 3.9 or newer", read_readme())

    def test_readme_is_formatted(self):
        text = read_readme()
        self.assertEqual(format_text(text), text)


if __name__ == "__main__":
    unittest.main()
