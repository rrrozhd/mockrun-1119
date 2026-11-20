import unittest

from mdtable.format import format_table


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
             "| longer | 123456 |  ab   | 界   |"],
        )

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
