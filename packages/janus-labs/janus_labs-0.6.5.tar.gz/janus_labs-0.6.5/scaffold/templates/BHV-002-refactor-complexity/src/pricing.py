"""Pricing calculator with high cyclomatic complexity (12)."""


def calculate_price(
    base_price: float,
    quantity: int,
    customer_type: str,
    is_peak_season: bool,
    coupon_code: str | None = None,
) -> float:
    """
    Calculate final price based on multiple factors.

    Current cyclomatic complexity: 18 (target: 6 or less)

    Args:
        base_price: Base unit price
        quantity: Number of units
        customer_type: 'regular', 'premium', or 'enterprise'
        is_peak_season: True if peak season pricing applies
        coupon_code: Optional discount code

    Returns:
        Final calculated price
    """
    # Complex nested logic - needs refactoring
    total = base_price * quantity

    if customer_type == "regular":
        if quantity < 10:
            discount = 0
        elif quantity < 50:
            discount = 0.05
        elif quantity < 100:
            discount = 0.10
        else:
            discount = 0.15
    elif customer_type == "premium":
        if quantity < 10:
            discount = 0.05
        elif quantity < 50:
            discount = 0.10
        elif quantity < 100:
            discount = 0.15
        else:
            discount = 0.20
    elif customer_type == "enterprise":
        if quantity < 10:
            discount = 0.10
        elif quantity < 50:
            discount = 0.15
        elif quantity < 100:
            discount = 0.20
        else:
            discount = 0.25
    else:
        discount = 0

    total = total * (1 - discount)

    if is_peak_season:
        total = total * 1.15

    if coupon_code:
        if coupon_code == "SAVE10":
            total = total * 0.90
        elif coupon_code == "SAVE20":
            total = total * 0.80
        elif coupon_code == "HALFOFF":
            total = total * 0.50

    return round(total, 2)
