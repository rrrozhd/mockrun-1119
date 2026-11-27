import unittest

from mdtable.format import display_width, format_table


class FormatTableTests(unittest.TestCase):
    def check_table(self, source, expected):
        result = format_table(source)
        self.assertEqual(result, expected)
        self.assertEqual(len(result), len(source))
        self.assertEqual(format_table(result), result)

    def test_alignments_and_longest_cell_determine_padding(self):
        self.check_table(
            ["L|R|C|N", ":---|---:|:---:|---", "longer|123456|ab|界"],
            ["| L      |      R |   C   | N   |",
             "| :----- | -----: | :---: | --- |",
             "| longer | 123456 |  ab   | 界  |"],
        )

    def test_wide_characters_count_two_columns(self):
        self.check_table(
            ["Name|Left|Mid|Right", ":-|:-|:-:|-:",
             "東京都|x|日本|😀", "a|漢字漢字|b|c"],
            ["| Name   | Left     |  Mid  | Right |",
             "| :----- | :------- | :---: | ----: |",
             "| 東京都 | x        | 日本  |    😀 |",
             "| a      | 漢字漢字 |   b   |     c |"],
        )

    def test_fullwidth_forms_count_two_columns(self):
        self.check_table(
            ["a|b", "-|-", "ＡＢ|x"],
            ["| a    | b   |", "| ---- | --- |", "| ＡＢ | x   |"],
        )

    def test_combining_and_format_characters_count_zero_columns(self):
        decomposed = "été"  # "été" with combining acute accents
        emoji = "❤️"  # heart with a variation selector
        self.check_table(
            ["word|x", "-|-", decomposed + "|" + emoji],
            ["| word | x   |", "| ---- | --- |",
             "| " + decomposed + "  | " + emoji + "   |"],
        )

    def test_display_width(self):
        cases = {
            "": 0, "abc": 3, "界": 2, "日本語": 6, "😀": 2, "ＡＢ": 4,
            "é": 1, "​": 0, "a‍b": 2, "ｱ": 1,
        }
        for text, width in cases.items():
            with self.subTest(text=text):
                self.assertEqual(display_width(text), width)

    def test_narrow_centered_column_fits_the_marker(self):
        self.check_table(["|x|", "|:-:|"], ["|   x   |", "| :---: |"])

    def test_short_and_long_rows_extend_to_same_width(self):
        self.check_table(
            ["a|b", "---|---:", "|s|", "||z|third|"],
            ["| a   |    b |       |", "| --- | ---: | ----- |",
             "| s   |      |       |", "|     |    z | third |"],
        )

    def test_escaped_pipes_and_outer_pipes(self):
        self.check_table(
            ["a|b", "-|-", r"one\|two|tail\|", r"a\\|b", "|end||"],
            ["| a        | b      |", "| -------- | ------ |",
             r"| one\|two | tail\| |", r"| a\\      | b      |",
             "| end      |        |"],
        )
