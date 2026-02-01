"""Tests for pricing calculator - must pass before and after refactoring."""

import pytest
from src.pricing import calculate_price


class TestCalculatePrice:
    """Test suite for calculate_price function."""

    def test_regular_customer_small_quantity(self):
        """Regular customer, <10 units, no discount."""
        result = calculate_price(10.0, 5, "regular", False)
        assert result == 50.0

    def test_regular_customer_medium_quantity(self):
        """Regular customer, 11-49 units, 5% discount."""
        result = calculate_price(10.0, 20, "regular", False)
        assert result == 190.0  # 200 * 0.95

    def test_premium_customer_large_quantity(self):
        """Premium customer, 100+ units, 20% discount."""
        result = calculate_price(10.0, 150, "premium", False)
        assert result == 1200.0  # 1500 * 0.80

    def test_enterprise_customer_bulk(self):
        """Enterprise customer, 100+ units, 25% discount."""
        result = calculate_price(10.0, 200, "enterprise", False)
        assert result == 1500.0  # 2000 * 0.75

    def test_peak_season_surcharge(self):
        """Peak season adds 15% surcharge."""
        result = calculate_price(10.0, 5, "regular", True)
        assert result == 57.5  # 50 * 1.15

    def test_coupon_save10(self):
        """SAVE10 coupon gives 10% off."""
        result = calculate_price(10.0, 10, "regular", False, "SAVE10")
        assert result == 85.5  # 100 * 0.95 * 0.90

    def test_coupon_save20(self):
        """SAVE20 coupon gives 20% off."""
        result = calculate_price(10.0, 10, "regular", False, "SAVE20")
        assert result == 76.0  # 100 * 0.95 * 0.80

    def test_coupon_halfoff(self):
        """HALFOFF coupon gives 50% off."""
        result = calculate_price(10.0, 10, "regular", False, "HALFOFF")
        assert result == 47.5  # 100 * 0.95 * 0.50

    def test_unknown_customer_type(self):
        """Unknown customer type gets no discount."""
        result = calculate_price(10.0, 100, "unknown", False)
        assert result == 1000.0

    def test_invalid_coupon_ignored(self):
        """Invalid coupon code has no effect."""
        result = calculate_price(10.0, 5, "regular", False, "INVALID")
        assert result == 50.0

    def test_combined_discounts(self):
        """Enterprise + peak + coupon all apply."""
        # 100 units @ $10 = $1000
        # Enterprise 100+ = 25% off = $750
        # Peak season = +15% = $862.50
        # SAVE10 = -10% = $776.25
        result = calculate_price(10.0, 100, "enterprise", True, "SAVE10")
        assert result == 776.25

    def test_zero_quantity(self):
        """Zero quantity returns zero price."""
        result = calculate_price(10.0, 0, "regular", False)
        assert result == 0.0
