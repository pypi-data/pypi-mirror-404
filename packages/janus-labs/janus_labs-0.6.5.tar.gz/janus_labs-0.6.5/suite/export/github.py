"""GitHub Actions export helpers."""

from suite.comparison import ComparisonResult, ComparisonVerdict


def print_github_annotations(result: ComparisonResult) -> None:
    """
    Print GitHub Actions workflow commands.
    """
    for comparison in result.behavior_comparisons:
        if comparison.verdict == ComparisonVerdict.REGRESSION:
            print(f"::error title={comparison.behavior_id}::{comparison.message}")
        elif comparison.verdict == ComparisonVerdict.WARNING:
            print(f"::warning title={comparison.behavior_id}::{comparison.message}")

    if result.verdict == ComparisonVerdict.PASS:
        print(
            "::notice::Benchmark passed: "
            f"{result.headline_current:.1f} ({result.headline_delta_pct:+.1f}%)"
        )
    elif result.verdict == ComparisonVerdict.WARNING:
        print(
            "::warning::Benchmark warning: "
            f"{result.warnings} warnings, {result.regressions} regressions"
        )
    else:
        print(f"::error::Benchmark failed: {result.regressions} regressions detected")


def generate_github_summary(result: ComparisonResult) -> str:
    """
    Generate GitHub Actions job summary markdown.

    Returns:
        Markdown string for $GITHUB_STEP_SUMMARY
    """
    lines = [
        "# Janus Labs Benchmark Comparison",
        "",
        f"**Verdict:** {result.verdict.value.upper()}",
        f"**Headline:** {result.headline_current:.1f} ({result.headline_delta_pct:+.1f}%)",
        f"**Regressions:** {result.regressions}  **Warnings:** {result.warnings}",
        "",
        "| Behavior | Baseline | Current | Delta % | Verdict |",
        "|---|---:|---:|---:|---|",
    ]

    for comparison in result.behavior_comparisons:
        lines.append(
            f"| {comparison.behavior_id} | {comparison.baseline_score:.1f} "
            f"| {comparison.current_score:.1f} | {comparison.delta_pct:+.1f}% "
            f"| {comparison.verdict.value.upper()} |"
        )

    if result.new_halts:
        lines.extend(["", f"**New halts:** {', '.join(result.new_halts)}"])

    return "\n".join(lines)
