"""Registry of built-in benchmark suites."""

from suite.builtin import REFACTOR_STORM
from suite.builtin.hello_world import HELLO_WORLD


SUITES = {
    REFACTOR_STORM.suite_id: REFACTOR_STORM,
    HELLO_WORLD.suite_id: HELLO_WORLD,
}


def get_suite(suite_id: str):
    """Return a suite by ID, or None."""
    return SUITES.get(suite_id)


def list_suites() -> list[str]:
    """List available suite IDs."""
    return sorted(SUITES.keys())
