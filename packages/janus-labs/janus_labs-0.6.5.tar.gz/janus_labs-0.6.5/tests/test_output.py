"""Tests for CLI output formatting helpers."""

import sys
from io import StringIO

from cli.output import (
    print_verdict,
    print_detail,
    print_next_step,
    print_error,
    print_warning,
)


class TestGoldStandardOutput:
    """Tests for JL-163 gold standard output format."""

    def test_print_verdict_pass(self, capsys):
        """VERDICT PASS format: COMMAND PASS: summary."""
        print_verdict("SCORE", "PASS", "7.0/10 (threshold 6.0)")
        captured = capsys.readouterr()
        assert captured.out == "SCORE PASS: 7.0/10 (threshold 6.0)\n"

    def test_print_verdict_fail(self, capsys):
        """VERDICT FAIL format: COMMAND FAIL: summary."""
        print_verdict("SCORE", "FAIL", "4.0/10 (threshold 6.0)")
        captured = capsys.readouterr()
        assert captured.out == "SCORE FAIL: 4.0/10 (threshold 6.0)\n"

    def test_print_detail(self, capsys):
        """Detail format: - text."""
        print_detail("Tests: 7 passed, 0 failed")
        captured = capsys.readouterr()
        assert captured.out == "  - Tests: 7 passed, 0 failed\n"

    def test_print_next_step(self, capsys):
        """Next step format: Try: command."""
        print_next_step("janus-labs submit result.json --github <handle>")
        captured = capsys.readouterr()
        assert captured.out == "\nTry: janus-labs submit result.json --github <handle>\n"

    def test_full_output_sequence(self, capsys):
        """Full output follows gold standard pattern."""
        print_verdict("SCORE", "PASS", "7.0/10 (threshold 6.0)")
        print_detail("Tests: 7 passed, 0 failed")
        print_detail("Files changed: 1 (src/calculator.py)")
        print_next_step("janus-labs submit result.json")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        # Verify structure
        assert lines[0].startswith("SCORE PASS:")
        assert lines[1].startswith("  - Tests:")
        assert lines[2].startswith("  - Files changed:")
        assert lines[4].startswith("Try:")


class TestErrorOutput:
    """Tests for error and warning output."""

    def test_print_error_to_stderr(self, capsys):
        """Errors go to stderr."""
        print_error("Something went wrong")
        captured = capsys.readouterr()
        assert captured.err == "Error: Something went wrong\n"
        assert captured.out == ""

    def test_print_warning_to_stderr(self, capsys):
        """Warnings go to stderr."""
        print_warning("Something might be wrong")
        captured = capsys.readouterr()
        assert captured.err == "Warning: Something might be wrong\n"
        assert captured.out == ""
