"""Interactive CLI menu for Janus Labs (JL-210.3).

Provides guided workflows when janus-labs is invoked without arguments.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# Check for dumb terminal before importing questionary
def is_dumb_terminal() -> bool:
    """Check if we're in a dumb terminal that doesn't support fancy prompts."""
    return (
        os.environ.get('TERM') == 'dumb' or
        os.environ.get('NO_COLOR') is not None or
        not sys.stdout.isatty()
    )


def simple_select(prompt: str, choices: List[dict]) -> Optional[str]:
    """Numbered fallback for non-interactive terminals."""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        name = choice.get('name', choice.get('label', str(choice)))
        print(f"  [{i}] {name}")
    print(f"  [0] Cancel")
    print()

    while True:
        try:
            selection = input("> ").strip()
            if selection == '0':
                return None
            idx = int(selection)
            if 1 <= idx <= len(choices):
                return choices[idx - 1].get('value', choices[idx - 1].get('name'))
        except (ValueError, EOFError, KeyboardInterrupt):
            return None
        print("Invalid selection. Please enter a number.")


def simple_confirm(prompt: str) -> bool:
    """Simple Y/n confirmation for dumb terminals."""
    try:
        response = input(f"{prompt} [Y/n] ").strip().lower()
        return response in ('', 'y', 'yes')
    except (EOFError, KeyboardInterrupt):
        return False


def get_available_suites():
    """Get list of available benchmark suites."""
    from suite.registry import list_suites, get_suite
    suite_ids = list_suites()
    suites = []
    for sid in suite_ids:
        suite = get_suite(sid)
        if suite:
            suites.append({
                'id': suite.suite_id,
                'name': suite.name if hasattr(suite, 'name') else suite.suite_id,
                'description': suite.description if hasattr(suite, 'description') else '',
            })
    return suites


def main_menu():
    """Launch interactive main menu."""
    print("\n" + "=" * 60)
    print("  Janus Labs - 3DMark for AI Agents")
    print("=" * 60)
    print()

    MAIN_CHOICES = [
        {"name": "Run a benchmark suite", "value": "run"},
        {"name": "Initialize a new task workspace", "value": "init"},
        {"name": "Score a completed task", "value": "score"},
        {"name": "View available suites", "value": "list"},
        {"name": "Run smoke test (quick validation)", "value": "smoke"},
        {"name": "Help", "value": "help"},
        {"name": "Exit", "value": "exit"},
    ]

    if is_dumb_terminal():
        action = simple_select("What would you like to do?", MAIN_CHOICES)
    else:
        try:
            import questionary
            from questionary import Style

            JANUS_STYLE = Style([
                ('qmark', 'fg:cyan bold'),
                ('question', 'bold'),
                ('answer', 'fg:green'),
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:cyan bold'),
                ('selected', 'fg:green'),
            ])

            action = questionary.select(
                "What would you like to do?",
                choices=MAIN_CHOICES,
                style=JANUS_STYLE
            ).ask()
        except ImportError:
            # Fallback if questionary not installed
            action = simple_select("What would you like to do?", MAIN_CHOICES)

    if action == "run":
        return run_benchmark_flow()
    elif action == "init":
        return init_flow()
    elif action == "score":
        return score_flow()
    elif action == "list":
        return list_suites_flow()
    elif action == "smoke":
        return smoke_test_flow()
    elif action == "help":
        return show_help()
    elif action == "exit" or action is None:
        print("Goodbye!")
        return 0

    return 0


def run_benchmark_flow() -> int:
    """Guided flow for running a benchmark."""
    suites = get_available_suites()
    if not suites:
        print("No benchmark suites available.")
        return 1

    # Step 1: Select suite
    suite_choices = [
        {"name": f"{s['name']} - {s['description']}" if s['description'] else s['name'], "value": s['id']}
        for s in suites
    ]

    if is_dumb_terminal():
        suite = simple_select("Select a benchmark suite:", suite_choices)
    else:
        try:
            import questionary
            suite = questionary.select(
                "Select a benchmark suite:",
                choices=suite_choices
            ).ask()
        except ImportError:
            suite = simple_select("Select a benchmark suite:", suite_choices)

    if not suite:
        return 0

    # Step 2: Select scoring method
    SCORING_CHOICES = [
        {"name": "Backend judge (recommended, no API key needed)", "value": "backend"},
        {"name": "Local LLM judge (requires OPENAI_API_KEY)", "value": "local"},
        {"name": "Mock scoring (offline, deterministic)", "value": "mock"},
    ]

    if is_dumb_terminal():
        scoring = simple_select("Select scoring method:", SCORING_CHOICES)
    else:
        try:
            import questionary
            scoring = questionary.select(
                "Select scoring method:",
                choices=SCORING_CHOICES
            ).ask()
        except ImportError:
            scoring = simple_select("Select scoring method:", SCORING_CHOICES)

    if not scoring:
        return 0

    # Step 3: Output format
    FORMAT_CHOICES = [
        {"name": "JSON only", "value": "json"},
        {"name": "HTML report", "value": "html"},
        {"name": "Both JSON and HTML", "value": "both"},
    ]

    if is_dumb_terminal():
        output_format = simple_select("Output format:", FORMAT_CHOICES)
    else:
        try:
            import questionary
            output_format = questionary.select(
                "Output format:",
                choices=FORMAT_CHOICES
            ).ask()
        except ImportError:
            output_format = simple_select("Output format:", FORMAT_CHOICES)

    if not output_format:
        return 0

    # Step 4: Confirm
    print(f"\nConfiguration:")
    print(f"  Suite: {suite}")
    print(f"  Scoring: {scoring}")
    print(f"  Format: {output_format}")
    print()

    if is_dumb_terminal():
        confirm = simple_confirm("Run benchmark?")
    else:
        try:
            import questionary
            confirm = questionary.confirm("Run benchmark?").ask()
        except ImportError:
            confirm = simple_confirm("Run benchmark?")

    if not confirm:
        print("Cancelled.")
        return 0

    # Build and execute command
    from cli.main import cmd_run
    import argparse

    args = argparse.Namespace(
        suite=suite,
        output="result.json",
        format=output_format,
        judge=(scoring == "local"),
        mock=(scoring == "mock"),
        model="gpt-4o",
        no_interactive=False,
    )
    return cmd_run(args)


def init_flow() -> int:
    """Guided flow for initializing a task workspace."""
    suites = get_available_suites()
    if not suites:
        print("No benchmark suites available.")
        return 1

    # Select suite
    suite_choices = [{"name": s['name'], "value": s['id']} for s in suites]

    if is_dumb_terminal():
        suite_id = simple_select("Select a benchmark suite:", suite_choices)
    else:
        try:
            import questionary
            suite_id = questionary.select(
                "Select a benchmark suite:",
                choices=suite_choices
            ).ask()
        except ImportError:
            suite_id = simple_select("Select a benchmark suite:", suite_choices)

    if not suite_id:
        return 0

    # Get behaviors for selected suite
    from suite.registry import get_suite
    suite = get_suite(suite_id)
    if not suite or not suite.behaviors:
        print(f"No behaviors found for suite: {suite_id}")
        return 1

    behavior_choices = [
        {"name": f"{b.behavior_id}: {b.name}", "value": b.behavior_id}
        for b in suite.behaviors
    ]

    if is_dumb_terminal():
        behavior = simple_select("Select a behavior:", behavior_choices)
    else:
        try:
            import questionary
            behavior = questionary.select(
                "Select a behavior:",
                choices=behavior_choices
            ).ask()
        except ImportError:
            behavior = simple_select("Select a behavior:", behavior_choices)

    if not behavior:
        return 0

    # Execute init
    from cli.main import cmd_init
    import argparse

    args = argparse.Namespace(
        suite=suite_id,
        behavior=behavior,
        output="./janus-task",
    )
    return cmd_init(args)


def score_flow() -> int:
    """Guided flow for scoring a completed task."""
    # Check if we're in a workspace
    workspace = Path.cwd()
    task_file = workspace / ".janus-task.json"

    if not task_file.exists():
        print("Not in a Janus Labs task workspace.")
        print("Navigate to a janus-task directory first.")
        return 1

    print(f"Scoring workspace: {workspace}")

    # Ask about judge scoring
    JUDGE_CHOICES = [
        {"name": "Outcome-only (fast, no API key)", "value": False},
        {"name": "With LLM judge (slower, needs API key)", "value": True},
    ]

    if is_dumb_terminal():
        use_judge = simple_select("Scoring mode:", JUDGE_CHOICES)
    else:
        try:
            import questionary
            use_judge = questionary.select(
                "Scoring mode:",
                choices=JUDGE_CHOICES
            ).ask()
        except ImportError:
            use_judge = simple_select("Scoring mode:", JUDGE_CHOICES)

    if use_judge is None:
        return 0

    # Execute score
    from cli.main import cmd_score
    import argparse

    args = argparse.Namespace(
        workspace=".",
        output="result.json",
        judge=use_judge,
        model="gpt-4o",
        bundle=None,
        agent=None,
        agent_model=None,
    )
    return cmd_score(args)


def list_suites_flow() -> int:
    """Show available benchmark suites."""
    suites = get_available_suites()

    print("\nAvailable Benchmark Suites:")
    print("-" * 40)
    for s in suites:
        print(f"  {s['id']}: {s['name']}")
        if s['description']:
            print(f"      {s['description']}")
    print()

    return 0


def smoke_test_flow() -> int:
    """Run quick smoke test."""
    print("Running smoke test with mock data...")
    print("Note: This validates installation, not your agent config.")
    print()

    from cli.main import cmd_smoke_test
    import argparse

    args = argparse.Namespace(
        suite="refactor-storm",
        behavior="BHV-001-test-cheating",
        submit=False,
        github=None,
        model="gpt-4o",
        copy=False,
        output=None,
    )
    return cmd_smoke_test(args)


def show_help() -> int:
    """Show help text."""
    print("""
Janus Labs - 3DMark for AI Agents

COMMANDS:
  run           Run a full benchmark suite
  init          Initialize a task workspace for benchmarking your agent
  score         Score a completed task
  compare       Compare two results for regression
  submit        Submit results to leaderboard
  smoke-test    Quick validation with mock data

QUICKSTART:
  1. janus-labs init --behavior BHV-001-test-cheating
  2. cd janus-task && <run your agent>
  3. janus-labs score -o result.json
  4. janus-labs submit result.json --github <handle>

OPTIONS:
  --help        Show full command help
  --version     Show version number

For detailed command help:
  janus-labs run --help
  janus-labs init --help
  janus-labs score --help
""")
    return 0
