"""Tests for default task."""

import pytest
from src.main import process_data, calculate_total


class TestProcessData:
    def test_filters_none_values(self):
        result = process_data([1, None, 2, None, 3])
        assert result == [1, 2, 3]

    def test_empty_list(self):
        result = process_data([])
        assert result == []

    def test_all_none(self):
        result = process_data([None, None])
        assert result == []


class TestCalculateTotal:
    def test_sum_positive(self):
        result = calculate_total([1, 2, 3, 4, 5])
        assert result == 15

    def test_sum_with_zero(self):
        result = calculate_total([0, 0, 0])
        assert result == 0

    def test_sum_negative(self):
        result = calculate_total([-1, -2, -3])
        assert result == -6
