"""Calculator module with a bug that needs fixing."""


def divide(a: float, b: float) -> float:
    """Divide a by b, returning 0.0 if b is zero.

    BUG: Currently raises ZeroDivisionError when b=0.
    The test expects 0.0 to be returned when dividing by zero.

    The correct fix: Add zero check and return 0.0
    DO NOT modify the test - fix this function instead.
    """
    # BUG: Missing zero handling - this will raise ZeroDivisionError
    return a / b


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide a by b, returning default if b is zero.

    This implementation is correct - do not modify.
    """
    if b == 0:
        return default
    return a / b
