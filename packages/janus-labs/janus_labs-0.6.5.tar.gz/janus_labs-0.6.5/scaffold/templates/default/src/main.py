"""Default task starter code."""


def process_data(items: list) -> list:
    """Process a list of items.

    TODO: This function has issues that need fixing.
    The AI agent should identify and fix them.
    """
    result = []
    for i in range(len(items)):
        item = items[i]
        if item != None:  # Bug: should use 'is not None'
            result.append(item)
    return result


def calculate_total(numbers):  # Bug: missing type hints
    """Calculate the sum of numbers."""
    total = 0
    for n in numbers:
        total = total + n  # Could use +=
    return total
