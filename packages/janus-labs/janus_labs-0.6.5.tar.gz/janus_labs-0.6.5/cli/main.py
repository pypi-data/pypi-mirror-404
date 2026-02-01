"""Command-line interface for Janus Labs."""

import argparse
import json
import os
import tempfile
from pathlib import Path
import sys

from config.detection import detect_config, detect_execution_context
from suite.comparison import (
    compare_results,
    comparison_to_dict,
    export_comparison_json,
    print_comparison_text,
)
from suite.export.github import generate_github_summary, print_github_annotations
from suite.export.html import export_html
from suite.export.json_export import export_json, load_json
from suite.registry import get_suite
from suite.runner import SuiteRunConfig, run_suite
from suite.thresholds import default_thresholds, load_thresholds

from cli.submit import cmd_submit, submit_result
from cli.output import print_benchmark_result, print_step, print_error, print_warning
from cli.clipboard import copy_to_clipboard, is_clipboard_available


__version__ = "0.6.3"

# Quickstart guide shown in --help and post-install
QUICKSTART_TEXT = """
================================================================================
  QUICKSTART
================================================================================

  Interactive mode (recommended for first-time users):
    janus-labs

  Run full benchmark suite (5 behaviors, backend-hosted judge):
    janus-labs refactor-storm

  Benchmark your own agent:
    1. janus-labs init --behavior BHV-001-test-cheating
    2. cd janus-task && <run your agent on TASK.md>
    3. janus-labs score -o result.json
    4. janus-labs submit result.json --github <handle>

================================================================================
  COMMON COMMANDS
================================================================================

  janus-labs                     Interactive menu (if no args)
  janus-labs refactor-storm      Run full suite with backend judge
  janus-labs refactor-storm --mock   Run offline with mock scores
  janus-labs smoke-test          Quick validation (mock data)
  janus-labs init                Initialize task workspace
  janus-labs score               Score completed task
  janus-labs submit              Submit to leaderboard

================================================================================
  TROUBLESHOOTING
================================================================================

  Command not found? Use the Python module directly:
    python -m janus_labs          # Note: underscore, not hyphen!

  Or add Scripts to PATH:
    Windows:  pip show janus-labs | findstr Location
              # Add <Location>\\Scripts to your PATH
    Unix:     pip show janus-labs | grep Location
              # Add <Location>/bin to your PATH

  Command aliases (all work the same):
    janus-labs    # Full name (recommended)
    janus         # Short alias

  Rate limit errors? The backend judge has limits per IP:
    - Use --mock for offline testing
    - Wait and retry (automatic backoff enabled)
"""


def main():
    parser = argparse.ArgumentParser(
        prog="janus-labs",
        description="Janus Labs - 3DMark for AI Agents",
        epilog=QUICKSTART_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--no-update-check",
        action="store_true",
        help="Skip version update check (useful for CI)",
    )
    # Make subparsers optional - launch interactive menu if no command given
    subparsers = parser.add_subparsers(dest="command", required=False)

    run_parser = subparsers.add_parser("run", help="Run a benchmark suite")
    run_parser.add_argument("--suite", required=True, help="Suite ID to run")
    run_parser.add_argument("--output", "-o", default="result.json", help="Output file")
    run_parser.add_argument(
        "--format",
        choices=["json", "html", "both"],
        default="json",
    )
    run_parser.add_argument(
        "--judge",
        action="store_true",
        help="Use local LLM-as-judge scoring (requires API key)",
    )
    run_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock scoring (offline, deterministic fake scores)",
    )
    run_parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model for judge scoring (default: gpt-4o)",
    )
    run_parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable prompts, auto-fallback to mock on rate limit (JL-210.2)",
    )
    run_parser.add_argument(
        "--request-delay",
        type=float,
        default=1.2,
        help="Delay between judge API calls in seconds (default: 1.2s, ~50 RPM)",
    )

    compare_parser = subparsers.add_parser("compare", help="Compare two results")
    compare_parser.add_argument("baseline", help="Baseline result JSON")
    compare_parser.add_argument("current", help="Current result JSON")
    compare_parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Regression threshold (%%)",
    )
    compare_parser.add_argument(
        "--config",
        "-c",
        help="Threshold config YAML file (default: use suite defaults)",
    )
    compare_parser.add_argument(
        "--output",
        "-o",
        help="Output comparison result to JSON file",
    )
    compare_parser.add_argument(
        "--format",
        choices=["text", "json", "github"],
        default="text",
        help="Output format (github = GitHub Actions annotations)",
    )

    export_parser = subparsers.add_parser("export", help="Export result to format")
    export_parser.add_argument("input", help="Input JSON result")
    export_parser.add_argument("--format", choices=["html", "json"], required=True)
    export_parser.add_argument("--output", "-o", help="Output file")

    baseline_parser = subparsers.add_parser("baseline", help="Manage baselines")
    baseline_sub = baseline_parser.add_subparsers(dest="baseline_command", required=True)
    update_parser = baseline_sub.add_parser("update", help="Update baseline from current result")
    update_parser.add_argument("result", help="Current result JSON to promote to baseline")
    update_parser.add_argument("--output", "-o", default="baseline.json", help="Baseline output path")
    update_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing baseline")

    show_parser = baseline_sub.add_parser("show", help="Show baseline info")
    show_parser.add_argument("baseline", help="Baseline JSON file")

    # Submit command (E6 Community Platform)
    submit_parser = subparsers.add_parser("submit", help="Submit results to leaderboard")
    submit_parser.add_argument("result_file", help="Path to result.json")
    submit_parser.add_argument(
        "--dry-run", action="store_true", help="Show payload without submitting"
    )
    submit_parser.add_argument(
        "--github", type=str, help="GitHub handle for attribution"
    )
    submit_parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip backend LLM judging (submit score only)",
    )

    # Init command (E7 Agent Execution)
    init_parser = subparsers.add_parser("init", help="Initialize task workspace for all behaviors in suite")
    init_parser.add_argument("--suite", default="refactor-storm", help="Suite ID (default: refactor-storm)")
    init_parser.add_argument(
        "--output", "-o",
        default="./janus-task",
        help="Output directory for workspaces (behaviors in subdirs)",
    )

    # Score command (E7 Agent Execution)
    score_parser = subparsers.add_parser("score", help="Score completed task")
    score_parser.add_argument(
        "--workspace", "-w",
        default=".",
        help="Path to task workspace (default: current directory)",
    )
    score_parser.add_argument(
        "--output", "-o",
        default="result.json",
        help="Output result to JSON file (default: result.json)",
    )
    score_parser.add_argument(
        "--judge",
        action="store_true",
        help="Enable LLM-as-judge scoring via DeepEval GEval (requires API key)",
    )
    score_parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model for judge scoring (default: gpt-4o)",
    )
    score_parser.add_argument(
        "--bundle",
        help="Path to bundle.json for judge scoring (optional, uses mock if not provided)",
    )
    score_parser.add_argument(
        "--agent",
        help="Agent identifier (auto-detected if not specified: claude-code, github-copilot, gemini-cli, codex, manual)",
    )
    score_parser.add_argument(
        "--agent-model",
        help="Model used by the agent (auto-detected if not specified: opus-4.5, gpt-5.2, gemini-3-pro)",
    )

    # Status command - show workspace context
    status_parser = subparsers.add_parser("status", help="Show current workspace status")
    status_parser.add_argument(
        "--workspace", "-w",
        default=".",
        help="Path to workspace (default: current directory)",
    )

    # Helper to add smoke-test arguments (shared between smoke-test and deprecated bench)
    def _add_smoke_test_args(p):
        p.add_argument("--suite", default="refactor-storm", help="Suite ID (default: refactor-storm)")
        p.add_argument("--behavior", default="BHV-001-test-cheating", help="Behavior ID (default: BHV-001-test-cheating)")
        p.add_argument("--submit", action="store_true", help="Submit results to public leaderboard")
        p.add_argument("--github", type=str, help="GitHub handle for attribution (requires --submit)")
        p.add_argument("--model", default="gpt-4o", help="LLM model for judge scoring (default: gpt-4o)")
        p.add_argument("--no-copy", dest="copy", action="store_false", help="Don't copy share URL to clipboard after submit")
        p.add_argument("--output", "-o", help="Output result to JSON file (default: temp file)")

    # Smoke-test command (primary) - Quick validation with mock data
    smoke_parser = subparsers.add_parser(
        "smoke-test",
        help="Quick validation with mock data (does NOT benchmark your agent config)",
    )
    _add_smoke_test_args(smoke_parser)

    # Bench command (deprecated alias) - Hidden from help
    bench_parser = subparsers.add_parser(
        "bench",
        help=argparse.SUPPRESS,  # Hide from --help
    )
    _add_smoke_test_args(bench_parser)

    # JL-210.6: Register suite aliases as hidden subcommands
    # e.g., `janus-labs refactor-storm` -> `janus-labs run --suite refactor-storm`
    from suite.registry import list_suites
    for suite_id in list_suites():
        alias_parser = subparsers.add_parser(
            suite_id,
            help=argparse.SUPPRESS,  # Hidden from --help
        )
        alias_parser.add_argument(
            "--mock", action="store_true",
            help="Use mock scoring (offline, deterministic)",
        )
        alias_parser.add_argument(
            "--judge", action="store_true",
            help="Use local LLM judge (requires API key)",
        )
        alias_parser.add_argument(
            "--output", "-o", default="result.json",
            help="Output file",
        )
        alias_parser.add_argument(
            "--format", choices=["json", "html", "both"], default="json",
        )
        alias_parser.add_argument(
            "--no-interactive", action="store_true",
            help="Disable prompts on rate limit",
        )
        alias_parser.add_argument(
            "--model", default="gpt-4o",
            help="LLM model for judge scoring",
        )
        alias_parser.add_argument(
            "--request-delay", type=float, default=1.2,
            help="Delay between judge API calls in seconds (default: 1.2s)",
        )

    args = parser.parse_args()

    # JL-230: Version update check (skip if --no-update-check or in CI)
    if not getattr(args, 'no_update_check', False):
        from cli.version_check import check_for_updates
        check_for_updates(__version__)

    # JL-210.3: Launch interactive menu if no command given
    if args.command is None:
        from cli.interactive import main_menu
        return main_menu()

    if args.command == "run":
        return cmd_run(args)
    if args.command == "compare":
        return cmd_compare(args)
    if args.command == "export":
        return cmd_export(args)
    if args.command == "baseline":
        return cmd_baseline(args)
    if args.command == "submit":
        return cmd_submit(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "score":
        return cmd_score(args)
    if args.command == "smoke-test":
        return cmd_smoke_test(args)
    if args.command == "bench":
        # Deprecation warning for bench command
        print("=" * 60)
        print("  DEPRECATION WARNING: 'janus bench' renamed to 'janus smoke-test'")
        print("=" * 60)
        print()
        print("  This command uses MOCK data and does NOT benchmark your agent.")
        print()
        print("  To benchmark your actual agent, use:")
        print("    janus-labs init --behavior BHV-001")
        print("    cd janus-task && <run your agent>")
        print("    janus-labs score -o result.json")
        print("    janus-labs submit result.json --github <handle>")
        print()
        return cmd_smoke_test(args)
    if args.command == "status":
        return cmd_status(args)

    # JL-210.6: Handle suite aliases
    # Check if command is a known suite ID
    from suite.registry import list_suites, get_suite
    known_suites = list_suites()
    if args.command in known_suites:
        # Convert alias to run command args
        args.suite = args.command
        return cmd_run(args)

    # Unknown command - show helpful error with suggestions
    print(f"Unknown command: {args.command}", file=sys.stderr)
    print(file=sys.stderr)
    print("Available commands:", file=sys.stderr)
    print("  run, init, score, compare, submit, smoke-test, status", file=sys.stderr)
    print(file=sys.stderr)
    print("Suite shortcuts (aliases for 'run --suite <name>'):", file=sys.stderr)
    for sid in known_suites:
        print(f"  {sid}", file=sys.stderr)
    print(file=sys.stderr)
    print("Run 'janus-labs --help' for more information.", file=sys.stderr)
    return 1


def _mock_execute_fn(rollout_index: int, behavior_id: str) -> dict:
    """Hash-based stub for testing without LLM. Produces deterministic fake scores."""
    value = abs(hash(f"{behavior_id}:{rollout_index}")) % 100
    score = 0.6 + (value / 250.0)
    return {"score": min(score, 0.99)}


# Alias for backwards compatibility
_default_execute_fn = _mock_execute_fn


def _create_backend_judge_execute_fn(suite, config_metadata, interactive: bool = True, request_delay: float = 1.2):
    """
    Create an execute function that uses backend-hosted LLM judging
    with rate limiting resilience (JL-210.2).

    This calls the Janus Labs /api/judge endpoint with circuit breaker
    and exponential backoff, eliminating the need for users to have
    their own API key.

    Args:
        suite: BenchmarkSuite containing behavior specs
        config_metadata: Configuration metadata for fingerprinting
        interactive: Whether to prompt user on rate limit (default: True)
        request_delay: Seconds between API calls to avoid rate limits (default: 1.2s)

    Returns:
        Execute function compatible with run_suite()
    """
    from gauge.resilience import ResilientJudgeClient

    # Backend endpoint
    BACKEND_URL = os.environ.get(
        "JANUS_BACKEND_URL",
        "https://fulfilling-courtesy-production-9c2c.up.railway.app"
    )

    # Create resilient client with circuit breaker and request throttling
    client = ResilientJudgeClient(
        base_url=BACKEND_URL,
        interactive=interactive,
        request_spacing=request_delay,
    )

    # Build behavior lookup for O(1) access
    behavior_map = {b.behavior_id: b for b in suite.behaviors}

    def execute_fn(rollout_index: int, behavior_id: str) -> dict:
        behavior = behavior_map.get(behavior_id)
        if behavior is None:
            print(f"Warning: Unknown behavior {behavior_id}", file=sys.stderr)
            return {"score": 0.0, "status": "SKIPPED", "error": "Unknown behavior"}

        # Check if we should use mock (circuit open + user chose mock)
        if client.should_use_mock:
            # Use deterministic mock scoring
            value = abs(hash(f"{behavior_id}:{rollout_index}")) % 100
            score = 0.6 + (value / 250.0)
            return {
                "score": min(score, 0.99),
                "status": "OK",
                "judge_method": "mock_fallback"
            }

        # Create mock bundle for backend judging
        mock_diff = f"""
# Mock solution for {behavior.name}
# Rollout {rollout_index}

def solution():
    '''Implementation of {behavior_id}'''
    pass
"""
        payload = {
            "behavior_id": behavior_id,
            "config_fingerprint": config_metadata.config_hash[:12] if config_metadata.config_hash else "default12345",
            "rollouts": [{
                "prompt": f"Task: {behavior.name}\n{behavior.description}",
                "response": f"Agent completed task {behavior_id}",
                "repo_diff": mock_diff,
                "test_output": "All tests passed (mock)",
            }],
            "behavior_name": behavior.name,
            "behavior_description": behavior.description,
        }

        result = client.judge(payload)

        if result.success:
            return {
                "score": result.score,
                "status": "OK",
                "judge_method": "backend"
            }
        else:
            return {
                "score": None,
                "status": result.status,
                "error": result.error,
                "judge_method": "backend_failed"
            }

    return execute_fn


def _create_geval_execute_fn(suite, model: str):
    """
    Create an execute function that uses GEval LLM-as-judge scoring.

    This replaces the hash stub with real LLM evaluation, providing
    differentiated scores based on qualitative assessment.

    Args:
        suite: BenchmarkSuite containing behavior specs
        model: LLM model for judging (e.g., gpt-4o, claude-3-5-sonnet)

    Returns:
        Execute function compatible with run_suite()
    """
    from gauge.judge import score_with_judge, create_mock_bundle

    # Build behavior lookup for O(1) access
    behavior_map = {b.behavior_id: b for b in suite.behaviors}

    def execute_fn(rollout_index: int, behavior_id: str) -> dict:
        behavior = behavior_map.get(behavior_id)
        if behavior is None:
            print(f"Warning: Unknown behavior {behavior_id}", file=sys.stderr)
            return {"score": 0.0}

        # Create mock bundle for GEval evaluation
        # In real usage, this would contain actual agent execution artifacts
        mock_diff = f"""
# Mock solution for {behavior.name}
# Rollout {rollout_index}

def solution():
    '''Implementation of {behavior_id}'''
    # Code would be captured from actual agent execution
    pass
"""
        bundle = create_mock_bundle(
            code_diff=mock_diff,
            test_output="All tests passed (mock)",
            exit_code="success",
        )

        # Use outcome score of 0.7 as baseline (reasonable mock performance)
        # Real implementation would use actual outcome-based scoring
        baseline_outcome = 0.7

        try:
            result = score_with_judge(
                behavior=behavior,
                bundle=bundle,
                outcome_score=baseline_outcome,
                model=model,
            )
            return {"score": result.combined_score}
        except ValueError as e:
            print(f"Judge error: {e}", file=sys.stderr)
            return {"score": 0.0}

    return execute_fn


def cmd_init(args) -> int:
    """Initialize task workspaces for all behaviors in suite."""
    from scaffold.workspace import init_workspace

    suite = get_suite(args.suite)
    if suite is None:
        print(f"Unknown suite: {args.suite}", file=sys.stderr)
        print("Try: Use 'refactor-storm' (default) or check available suites.", file=sys.stderr)
        return 1

    base_dir = Path(args.output)
    if base_dir.exists() and any(base_dir.iterdir()):
        print(f"Directory not empty: {base_dir}", file=sys.stderr)
        print(f"Try: janus-labs init --output ./janus-task-2", file=sys.stderr)
        print(f"  Or: rm -rf {base_dir} && janus-labs init", file=sys.stderr)
        return 1

    # Create base directory
    base_dir.mkdir(parents=True, exist_ok=True)

    # Initialize workspace for each behavior in subdirectories
    initialized = []
    for behavior in suite.behaviors:
        behavior_dir = base_dir / behavior.behavior_id
        metadata = init_workspace(behavior_dir, suite, behavior)
        initialized.append(behavior)

        # UX-005: Auto-add result.json to .gitignore per workspace
        gitignore_path = behavior_dir / ".gitignore"
        gitignore_entries = ["result.json", "*.bundle.json"]
        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            new_entries = [e for e in gitignore_entries if e not in existing]
            if new_entries:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Janus Labs artifacts\n")
                    for entry in new_entries:
                        f.write(f"{entry}\n")
        else:
            with open(gitignore_path, "w") as f:
                f.write("# Janus Labs artifacts\n")
                for entry in gitignore_entries:
                    f.write(f"{entry}\n")

    # Summary output
    print(f"Initialized {len(initialized)} behavior workspaces in: {base_dir}")
    print(f"  Suite: {suite.suite_id} v{suite.version}")
    print()
    for b in initialized:
        print(f"  {b.behavior_id}/")
        print(f"    {b.name}")
    print()
    print("Next steps:")
    print(f"  1. cd {base_dir}/<behavior-id>")
    print("  2. Open in VS Code and run your AI agent on each task")
    print("  3. Run: janus-labs score  (in each behavior directory)")

    return 0


def cmd_score(args) -> int:
    """Score a completed task workspace."""
    from scaffold.workspace import load_task_metadata
    from scaffold.scorer import score_outcome

    workspace = Path(args.workspace).resolve()

    metadata = load_task_metadata(workspace)
    if metadata is None:
        print("Not a Janus Labs task workspace.", file=sys.stderr)
        print("No .janus-task.json found.", file=sys.stderr)
        print("Try: cd into a janus-task directory, or use --workspace <path>", file=sys.stderr)
        return 1

    print(f"Scoring task: {metadata.behavior_id}")
    print(f"  Suite: {metadata.suite_id}")
    print(f"  Behavior: {metadata.behavior_name}")
    print()

    # Outcome-based scoring (always runs)
    result = score_outcome(
        workspace_dir=workspace,
        behavior_id=metadata.behavior_id,
        threshold=metadata.threshold,
        rubric=metadata.rubric,
    )

    # Track if no changes were made
    no_changes = not result.git_diff["files_changed"]

    # Display prominent score banner (JL-102)
    from cli.output import print_score_banner, print_detail, print_next_step

    print_score_banner(
        score=result.raw_score,
        threshold=metadata.threshold,
        passed=result.passed_threshold,
        behavior_name=metadata.behavior_name,
    )

    # Details breakdown
    tests = result.test_results
    print_detail(f"Tests: {tests['passed']} passed, {tests['failed']} failed")

    files_changed = result.git_diff["files_changed"]
    if files_changed:
        file_list = ", ".join(files_changed[:3])
        if len(files_changed) > 3:
            file_list += f" (+{len(files_changed) - 3} more)"
        print_detail(f"Files changed: {len(files_changed)} ({file_list})")
    else:
        print_detail("Files changed: 0 (no committed changes)")

    # Scoring notes (filter to most relevant)
    for note in result.scoring_notes:
        if note not in ["No changes made"]:  # Skip redundant notes
            print_detail(note)

    # Next step suggestion
    if no_changes:
        print_next_step("git add . && git commit -m 'Implement solution'")

    # Judge scoring (optional, requires --judge flag)
    judge_result = None
    if args.judge:
        print()
        print("=" * 60)
        print("LLM-as-Judge Scoring (GEval)")
        print("=" * 60)

        try:
            from gauge.judge import score_with_judge, load_bundle_from_file, create_mock_bundle
            from forge.behavior import BehaviorSpec

            # Reconstruct BehaviorSpec from metadata
            behavior = BehaviorSpec(
                behavior_id=metadata.behavior_id,
                name=metadata.behavior_name,
                description=metadata.behavior_description,
                rubric=metadata.rubric,
                threshold=metadata.threshold,
                disconfirmers=metadata.disconfirmers,
                taxonomy_code=metadata.taxonomy_code,
            )

            # Load bundle: explicit file > captured bundle > mock bundle
            if args.bundle:
                print(f"Loading bundle from: {args.bundle}")
                bundle = load_bundle_from_file(args.bundle)
            elif result.bundle:
                # E8-S2: Use real captured bundle from workspace
                print("Using captured workspace bundle")
                bundle = result.bundle
            else:
                print("Using mock bundle (no bundle captured)")
                bundle = create_mock_bundle(
                    code_diff=result.git_diff.get("patch", ""),
                    test_output=result.test_results.get("output", ""),
                    exit_code="success" if result.passed_threshold else "error",
                )

            print(f"Model: {args.model}")
            print()

            judge_result = score_with_judge(
                behavior=behavior,
                bundle=bundle,
                outcome_score=result.normalized_score,
                model=args.model,
            )

            print(f"GEval Score: {judge_result.geval_score_10:.1f}/10")
            print(f"Reason: {judge_result.reason}")
            print()
            print(f"Combined Score: {judge_result.combined_score_10:.1f}/10")
            print("  (40% outcome + 60% qualitative)")

        except ValueError as e:
            print(f"Judge scoring failed: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Judge scoring error: {e}", file=sys.stderr)
            # Continue without judge score

    # Output results
    if args.output:
        # Detect execution context (agent, model, interface)
        exec_ctx = detect_execution_context(
            workspace_path=workspace,
            agent_override=getattr(args, "agent", None),
            model_override=getattr(args, "agent_model", None),
        )

        output_data = {
            "behavior_id": result.behavior_id,
            "score": result.raw_score,  # Required by submit command
            "outcome_score": result.raw_score,
            "normalized_score": result.normalized_score,
            "passed": result.passed_threshold,
            "threshold": metadata.threshold,
            "notes": result.scoring_notes,
            "git_diff": result.git_diff,
            "test_results": result.test_results,
            "workspace_hash": result.workspace_hash,  # Anti-cheat validation
            # Execution context for leaderboard segmentation
            "agent": exec_ctx.agent,
            "model": exec_ctx.model,
            "execution_context": {
                "agent": exec_ctx.agent,
                "model": exec_ctx.model,
                "interface": exec_ctx.interface,
                "ide": exec_ctx.ide,
                "detected": exec_ctx.detected,
            },
        }

        if judge_result:
            output_data["judge"] = {
                "geval_score": judge_result.geval_score_10,
                "combined_score": judge_result.combined_score_10,
                "reason": judge_result.reason,
                "model": judge_result.model,
            }

        Path(args.output).write_text(json.dumps(output_data, indent=2))
        print_detail(f"Results saved to: {args.output}")

        # E8-S2: Save bundle for future GEval evaluation
        if result.bundle:
            bundle_path = Path(args.output).with_suffix(".bundle.json")
            bundle_path.write_text(json.dumps(result.bundle, indent=2))
            print_detail(f"Bundle saved to: {bundle_path}")

        # Next step: submit to leaderboard
        if result.passed_threshold:
            print_next_step(f"janus-labs submit {args.output} --github <handle>")

    return 0 if result.passed_threshold else 1


def cmd_status(args) -> int:
    """Show current workspace status."""
    import subprocess

    workspace = Path(args.workspace)
    task_file = workspace / ".janus-task.json"

    if not task_file.exists():
        print("Not in a Janus workspace.", file=sys.stderr)
        print("Try: janus-labs init --behavior <behavior-id>", file=sys.stderr)
        return 1

    task_data = json.loads(task_file.read_text())

    print("Janus Labs Workspace Status")
    print("=" * 40)
    print(f"  Behavior: {task_data.get('behavior_id', 'unknown')}")
    print(f"  Suite:    {task_data.get('suite_id', 'unknown')}")
    print(f"  Created:  {task_data.get('created_at', 'unknown')}")

    committed = None
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=workspace,
        )
        changes = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        committed = changes == 0
        print(f"  Changes:  {'Committed' if committed else f'{changes} uncommitted files'}")
    except Exception:
        print("  Changes:  Unable to determine")

    print()
    if committed is False:
        print("Next: git add . && git commit -m 'solution' && janus-labs score")
    else:
        print("Next: janus-labs score")

    return 0


def cmd_smoke_test(args) -> int:
    """
    Quick validation with mock data (smoke test).

    Detects config, runs GEval scoring with mock bundles, and optionally submits.
    NOTE: This does NOT benchmark your actual agent config - use init/score for that.
    """
    from scaffold.workspace import init_workspace

    # Step 1: Detect config
    print_step(1, 4, "Detecting config")
    config_metadata = detect_config(Path.cwd())
    if config_metadata.config_source == "custom":
        print(f"    Found: {', '.join(config_metadata.config_files)} (hash: {config_metadata.config_hash})")
    else:
        print("    Using default config")

    # Step 2: Get suite and behavior
    print_step(2, 4, "Loading behavior")
    suite = get_suite(args.suite)
    if suite is None:
        print_error(f"Unknown suite: {args.suite}")
        return 1

    behavior = None
    for b in suite.behaviors:
        if b.behavior_id == args.behavior:
            behavior = b
            break

    if behavior is None:
        print_error(f"Unknown behavior: {args.behavior}")
        print(f"Available behaviors in {args.suite}:")
        for b in suite.behaviors:
            print(f"  - {b.behavior_id}: {b.name}")
        return 1

    print(f"    Behavior: {behavior.behavior_id} - {behavior.name}")

    # Step 3: Score with GEval
    print_step(3, 4, f"Scoring with GEval ({args.model})")

    # Run the suite for single behavior
    config = SuiteRunConfig(suite=suite, config_metadata=config_metadata)
    execute_fn = _create_geval_execute_fn(suite, args.model)

    try:
        result = run_suite(config, execute_fn)
    except Exception as e:
        print_error(f"Scoring failed: {e}")
        return 1

    # Save result to file
    if args.output:
        output_path = Path(args.output)
    else:
        # Use temp file if no output specified
        fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="janus-bench-")
        os.close(fd)
        output_path = Path(tmp_path)

    export_json(result, str(output_path))
    print(f"    Score: {result.headline_score:.1f} (Grade {result.grade})")

    # Step 4: Submit if requested
    if args.submit:
        print_step(4, 4, "Submitting to leaderboard")
        try:
            submit_data = submit_result(
                str(output_path),
                github_handle=args.github,
                dry_run=False,
            )

            if submit_data.get("status") == "success":
                # Print rich result
                print_benchmark_result(
                    score=submit_data["score"],
                    rank=submit_data.get("rank"),
                    percentile=submit_data.get("percentile"),
                    share_url=submit_data.get("share_url"),
                )

                # Copy to clipboard if available and not disabled
                if args.copy and submit_data.get("share_url"):
                    if is_clipboard_available():
                        if copy_to_clipboard(submit_data["share_url"]):
                            print("\nCopied to clipboard!")
                        else:
                            print_warning("Could not copy to clipboard")

            return 0

        except RuntimeError as e:
            print_error(f"Submit failed: {e}")
            # Still show local result
            print_benchmark_result(
                score=result.headline_score,
                grade=result.grade,
            )
            print(f"\nResult saved to: {output_path}")
            return 1
    else:
        # Not submitting - show local result only
        print_step(4, 4, "Complete (not submitting)")
        print_benchmark_result(
            score=result.headline_score,
            grade=result.grade,
        )
        print(f"\nResult saved to: {output_path}")
        print("\nTo submit to leaderboard, run:")
        print(f"  janus-labs submit {output_path}")
        print("Or use: janus-labs smoke-test --submit")
        return 0


def cmd_run(args) -> int:
    """Run a benchmark suite."""
    suite = get_suite(args.suite)
    if suite is None:
        print(f"RUN FAILED: Unknown suite '{args.suite}'", file=sys.stderr)
        print(f"\n  Available suites: refactor-storm", file=sys.stderr)
        print(f"\n  Try: janus-labs run --suite refactor-storm", file=sys.stderr)
        return 1

    config_metadata = detect_config(Path.cwd())
    config = SuiteRunConfig(suite=suite, config_metadata=config_metadata)

    # Select execute function based on flags
    # Priority: --mock > --judge > default (backend)
    if args.mock:
        # Explicit mock mode for offline testing
        print("=" * 60)
        print("  MOCK MODE: Scores are SIMULATED (deterministic hash)")
        print("=" * 60)
        print()
        execute_fn = _mock_execute_fn
    elif args.judge:
        # Local LLM scoring (requires user's API key)
        print(f"Using local LLM-as-judge scoring (model: {args.model})")
        print("This requires OPENAI_API_KEY or ANTHROPIC_API_KEY.")
        print()
        execute_fn = _create_geval_execute_fn(suite, args.model)
    else:
        # Default: Backend-hosted judging (no local API key needed)
        print("Using backend-hosted LLM judging (no API key needed)")
        print()
        interactive = not getattr(args, 'no_interactive', False)
        request_delay = getattr(args, 'request_delay', 1.2)
        execute_fn = _create_backend_judge_execute_fn(suite, config_metadata, interactive=interactive, request_delay=request_delay)

    result = run_suite(config, execute_fn)

    output_path = Path(args.output)
    if args.format in ("json", "both"):
        export_json(result, str(output_path))
    if args.format in ("html", "both"):
        html_path = output_path.with_suffix(".html")
        export_html(result, str(html_path))

    # Gold standard output format
    from cli.output import print_verdict, print_detail, print_next_step
    from suite.result import BehaviorStatus

    # Check for judge failures (JL-210.1)
    judged_behaviors = [b for b in result.behavior_scores
                        if b.status in (BehaviorStatus.PASSED, BehaviorStatus.FAILED)]
    judge_failed_count = sum(1 for b in result.behavior_scores
                              if b.status == BehaviorStatus.JUDGE_FAILED)
    total_behaviors = len(result.behavior_scores)

    # Determine pass/fail based on governance and scores
    if judge_failed_count == total_behaviors:
        status = "INCOMPLETE"
    elif result.governance_flags.any_halted:
        status = "WARN"
    elif judge_failed_count > 0:
        status = "WARN"
    else:
        status = "PASS"
    print_verdict("RUN", status, f"Suite {suite.suite_id} complete")

    # Details breakdown
    if judge_failed_count > 0:
        print_detail(f"Headline score: {result.headline_score:.1f} ({result.grade}) - INCOMPLETE ({len(judged_behaviors)}/{total_behaviors} judged)")
    else:
        print_detail(f"Headline score: {result.headline_score:.1f} ({result.grade})")

    passed_count = sum(1 for b in result.behavior_scores if b.passed and b.status == BehaviorStatus.PASSED)
    print_detail(f"Behaviors: {passed_count}/{len(judged_behaviors)} passed")

    if result.governance_flags.any_halted:
        print_detail(f"Governance: {result.governance_flags.halted_count} halted")

    if args.judge:
        print_detail(f"Scored with GEval ({args.model})")

    print_detail(f"Results saved to: {args.output}")

    # Next step
    print_next_step(f"janus-labs compare baseline.json {args.output}")

    return 0


def cmd_compare(args) -> int:
    """Compare two results for regression."""
    baseline = load_json(args.baseline)
    current = load_json(args.current)

    if args.config:
        config = load_thresholds(args.config)
    else:
        config = default_thresholds(baseline.suite_id)

    if config.suite_id != baseline.suite_id:
        print("Threshold suite_id does not match baseline suite.", file=sys.stderr)
        return 2

    result = compare_results(baseline, current, config)

    if args.output:
        export_comparison_json(result, args.output)

    if args.format == "text":
        print_comparison_text(result)
    elif args.format == "json":
        print(json.dumps(comparison_to_dict(result), indent=2))
    elif args.format == "github":
        print_github_annotations(result)
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            Path(summary_path).write_text(generate_github_summary(result), encoding="utf-8")

    return result.exit_code


def cmd_export(args) -> int:
    """Export result to different format."""
    result = load_json(args.input)
    output = args.output

    if args.format == "html":
        if output is None:
            output = str(Path(args.input).with_suffix(".html"))
        export_html(result, output)
        return 0

    if args.format == "json":
        if output is None:
            output = str(Path(args.input).with_suffix(".json"))
        export_json(result, output)
        return 0

    return 1


def cmd_baseline(args) -> int:
    """Baseline management command."""
    if args.baseline_command == "update":
        return cmd_baseline_update(args)
    if args.baseline_command == "show":
        return cmd_baseline_show(args)
    return 1


def cmd_baseline_update(args) -> int:
    """Promote result to baseline."""
    result = load_json(args.result)
    output = Path(args.output)

    if output.exists() and not args.force:
        print(f"Baseline exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1

    export_json(result, str(output))
    print(f"Baseline updated: {output}")
    print(f"  Suite: {result.suite_id} v{result.suite_version}")
    print(f"  Score: {result.headline_score:.1f} ({result.grade})")
    return 0


def cmd_baseline_show(args) -> int:
    """Show baseline info."""
    result = load_json(args.baseline)
    print(f"Suite: {result.suite_id} v{result.suite_version}")
    print(f"Score: {result.headline_score:.1f} ({result.grade})")
    print(f"Comparability key: {result.comparability_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
