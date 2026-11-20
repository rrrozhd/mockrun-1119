import unittest

from mdtable.tables import find_tables, split_cells


class SplitCellsTest(unittest.TestCase):
    def test_outer_pipes_dropped(self):
        self.assertEqual(split_cells("| a | b |"), [" a ", " b "])

    def test_no_outer_pipes(self):
        self.assertEqual(split_cells("a | b"), ["a ", " b"])

    def test_escaped_pipe_stays_in_cell(self):
        self.assertEqual(split_cells(r"| a \| b | c |"), [r" a \| b ", " c "])

    def test_backslash_parity(self):
        self.assertEqual(split_cells("| a\\\\| b |"), [" a\\\\", " b "])
        self.assertEqual(split_cells("| a\\\\\\| b |"), [" a\\\\\\| b "])

    def test_empty_inner_cell_kept(self):
        self.assertEqual(split_cells("| a | |"), [" a ", " "])


class FindTablesTest(unittest.TestCase):
    def test_simple_table(self):
        lines = ["intro", "", "| a | b |", "|---|:-:|", "| 1 | 2 |", "", "outro"]
        self.assertEqual(find_tables(lines), [(2, 5)])

    def test_table_without_outer_pipes(self):
        self.assertEqual(find_tables(["a | b", "--- | ---", "1 | 2"]), [(0, 3)])

    def test_header_only_table(self):
        self.assertEqual(find_tables(["| a |", "| --- |"]), [(0, 2)])

    def test_table_ends_at_line_without_pipe(self):
        lines = ["| a |", "|---|", "| 1 |", "text"]
        self.assertEqual(find_tables(lines), [(0, 3)])

    def test_two_tables(self):
        lines = ["| a |", "|---|", "", "| b |", "|---|", "| 2 |"]
        self.assertEqual(find_tables(lines), [(0, 2), (3, 6)])

    def test_cell_count_mismatch_is_not_a_table(self):
        self.assertEqual(find_tables(["| a | b |", "|---|"]), [])

    def test_alignment_row_needs_a_pipe(self):
        # "---" under a line is a heading underline or a rule, not a table.
        self.assertEqual(find_tables(["| a |", "---"]), [])

    def test_invalid_alignment_cell(self):
        self.assertEqual(find_tables(["| a |", "| -x- |"]), [])

    def test_escaped_pipes_do_not_make_a_table(self):
        self.assertEqual(find_tables([r"a \| b", r"--- \| ---"]), [])

    def test_ragged_body_rows_belong_to_table(self):
        lines = ["| a | b |", "|---|---|", "| 1 |", "| 1 | 2 | 3 |"]
        self.assertEqual(find_tables(lines), [(0, 4)])

    def test_indented_code_is_not_a_table(self):
        self.assertEqual(find_tables(["    | a |", "    |---|"]), [])

    def test_table_in_backtick_fence_ignored(self):
        lines = ["```", "| a |", "|---|", "```", "| b |", "|---|"]
        self.assertEqual(find_tables(lines), [(4, 6)])

    def test_table_in_tilde_fence_ignored(self):
        lines = ["~~~md", "| a |", "|---|", "~~~"]
        self.assertEqual(find_tables(lines), [])

    def test_fence_closes_only_with_same_char_and_length(self):
        lines = ["````", "```", "~~~~", "| a |", "|---|", "````", "| b |", "|---|"]
        self.assertEqual(find_tables(lines), [(6, 8)])

    def test_unclosed_fence_runs_to_end(self):
        self.assertEqual(find_tables(["```", "| a |", "|---|"]), [])

    def test_indented_line_ends_table(self):
        self.assertEqual(find_tables(["a|b", "-|-", "    keep | verbatim"]), [(0, 2)])

    def test_fence_opener_with_pipe_ends_table(self):
        lines = ["a|b", "-|-", "~~~ demo|x", "| c | d |", "|---|---|", "~~~", "| e |", "|---|"]
        self.assertEqual(find_tables(lines), [(0, 2), (6, 8)])

    def test_even_backslash_run_leaves_pipe_structural(self):
        self.assertEqual(find_tables(["a\\\\|b", "-|-", "1\\\\|2"]), [(0, 3)])

    def test_odd_backslash_run_escapes_pipe(self):
        self.assertEqual(find_tables(["a\\\\\\|b", "-|-"]), [])

    def test_no_lines(self):
        self.assertEqual(find_tables([]), [])

    def test_no_table(self):
        self.assertEqual(find_tables(["# Title", "", "Some text.", "- item"]), [])

    def test_table_at_start_and_end_of_document(self):
        lines = ["| a |", "|---|", "| 1 |", "", "middle", "", "| b |", "|---|", "| 2 |"]
        self.assertEqual(find_tables(lines), [(0, 3), (6, 9)])

    def test_pipe_line_without_alignment_row(self):
        self.assertEqual(find_tables(["| a | b |", "| 1 | 2 |", "text"]), [])


if __name__ == "__main__":
    unittest.main()
