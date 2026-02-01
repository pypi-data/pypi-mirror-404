#!/usr/bin/env python3
"""
Module entry point for janus-labs CLI.

Enables running the CLI via:
    python -m janus_labs <command> [args]

This is the recommended fallback if 'janus-labs' is not in your PATH.

Examples:
    python -m janus_labs run --suite refactor-storm
    python -m janus_labs bench --submit
    python -m janus_labs submit result.json --github myhandle
"""

import sys


def main():
    """Entry point that delegates to CLI main."""
    try:
        from cli.main import main as cli_main
        return cli_main()
    except ImportError as e:
        # Provide helpful error if dependencies are missing
        print(f"Error: {e}", file=sys.stderr)
        print(file=sys.stderr)
        print("Janus Labs requires additional dependencies.", file=sys.stderr)
        print("Install with: pip install janus-labs", file=sys.stderr)
        print(file=sys.stderr)
        print("If you've already installed, ensure you're using the correct Python:", file=sys.stderr)
        print(f"  Current: {sys.executable}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
