"""Rich terminal output formatting for Janus Labs CLI."""

import sys


def _score_to_grade(score: float) -> str:
    """Convert 0-100 score to letter grade."""
    if score >= 95:
        return "S"
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def print_benchmark_result(
    score: float,
    grade: str | None = None,
    rank: int | None = None,
    total: int | None = None,
    percentile: float | None = None,
    share_url: str | None = None,
) -> None:
    """
    Print colorful benchmark result to terminal.

    Args:
        score: Score value (0-100)
        grade: Letter grade (S/A/B/C/D/F), computed if not provided
        rank: Rank position (e.g., 42)
        total: Total entries (e.g., 1234)
        percentile: Percentile value (e.g., 97.5 means top 2.5%)
        share_url: URL to share the result
    """
    if grade is None:
        grade = _score_to_grade(score)

    # Box characters
    line = "=" * 50

    print()
    print(line)
    print("  BENCHMARK RESULT")
    print(line)
    print(f"  Score: {score:.1f} (Grade {grade})")

    if rank is not None:
        if total is not None:
            print(f"  Rank: #{rank} of {total:,}")
        else:
            print(f"  Rank: #{rank}")

    if percentile is not None:
        # percentile from DB is cumulative, so "top X%" = 100 - percentile
        top_percent = 100.0 - percentile
        if top_percent < 1:
            print(f"  Percentile: Top {top_percent:.1f}%")
        else:
            print(f"  Percentile: Top {top_percent:.0f}%")

    if share_url:
        print()
        print(f"  Share your result: {share_url}")

    print(line)


def print_step(step: int, total: int, message: str, detail: str | None = None) -> None:
    """
    Print a progress step.

    Args:
        step: Current step number (1-indexed)
        total: Total number of steps
        message: Step message
        detail: Optional detail to show after message
    """
    prefix = f"[{step}/{total}]"
    if detail:
        print(f"{prefix} {message}... {detail}")
    else:
        print(f"{prefix} {message}...")


def print_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message to stderr."""
    print(f"Warning: {message}", file=sys.stderr)


# ============================================================================
# Score Banner Display (JL-102)
# Prominent score visualization after janus score completes
# ============================================================================


def print_score_banner(
    score: float,
    threshold: float,
    passed: bool,
    behavior_name: str | None = None,
) -> None:
    """
    Print prominent score banner with box and grade.

    Args:
        score: Raw score (0-10 scale)
        threshold: Passing threshold
        passed: Whether threshold was met
        behavior_name: Optional behavior name for context
    """
    # Convert to 100-scale for grade calculation
    score_100 = score * 10
    grade = _score_to_grade(score_100)

    # Status indicator
    status = "PASS" if passed else "FAIL"

    # Use ASCII box drawing (Windows console compatibility)
    print()
    print("+=======================================+")
    print(f"|  SCORE: {score_100:5.1f}/100   |   Grade: {grade:>2}   |")
    print("+---------------------------------------+")
    print(f"|  [{status:>4}]  threshold: {threshold * 10:>3.0f}             |")
    if behavior_name:
        # Truncate long names
        name = behavior_name[:33] if len(behavior_name) > 33 else behavior_name
        print(f"|  {name:<35} |")
    print("+=======================================+")
    print()


# ============================================================================
# Gold Standard Output Format (JL-163)
# Pattern: VERDICT line → Detail breakdown → Try: next step
# ============================================================================


def print_verdict(command: str, status: str, summary: str) -> None:
    """
    Print verdict line in gold standard format.

    Args:
        command: Command name (e.g., "SCORE", "RUN", "COMPARE")
        status: "PASS" or "FAIL"
        summary: Summary text (e.g., "7.0/10 (threshold 6.0)")

    Example:
        SCORE PASS: 7.0/10 (threshold 6.0)
    """
    print(f"{command} {status}: {summary}")


def print_detail(text: str) -> None:
    """
    Print a detail line in gold standard format.

    Args:
        text: Detail text to print

    Example:
        - Tests: 7 passed, 0 failed
    """
    print(f"  - {text}")


def print_next_step(command: str) -> None:
    """
    Print next step suggestion in gold standard format.

    Args:
        command: The command to suggest

    Example:
        Try: janus-labs submit result.json --github <handle>
    """
    print(f"\nTry: {command}")
