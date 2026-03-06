"""
Tests for input validators.
Covers all input validation functions.
"""

import pytest
from utils.validators import (
    is_valid_age,
    is_valid_months,
    is_valid_name,
    is_positive_number,
    sanitise_text,
    validate_goal_inputs,
)


class TestNameValidation:
    def test_valid_name(self):
        assert is_valid_name("Priya Sharma") is True

    def test_name_with_hyphen(self):
        assert is_valid_name("Mary-Jane") is True

    def test_name_with_apostrophe(self):
        assert is_valid_name("O'Brien") is True

    def test_name_too_short(self):
        assert is_valid_name("A") is False

    def test_name_with_numbers(self):
        assert is_valid_name("John123") is False

    def test_name_with_special_chars(self):
        assert is_valid_name("John@Doe!") is False


class TestAgeValidation:
    def test_valid_age(self):
        assert is_valid_age(30) is True

    def test_min_age(self):
        assert is_valid_age(16) is True

    def test_max_age(self):
        assert is_valid_age(100) is True

    def test_underage(self):
        assert is_valid_age(15) is False

    def test_over_max(self):
        assert is_valid_age(101) is False

    def test_string_age(self):
        assert is_valid_age("abc") is False


class TestPositiveNumber:
    def test_zero_valid(self):
        assert is_positive_number(0) is True

    def test_positive_float(self):
        assert is_positive_number(12345.67) is True

    def test_negative_invalid(self):
        assert is_positive_number(-1) is False

    def test_string_number(self):
        assert is_positive_number("12345") is True

    def test_invalid_string(self):
        assert is_positive_number("abc") is False


class TestMonthsValidation:
    def test_valid_months(self):
        assert is_valid_months(36) is True

    def test_min_months(self):
        assert is_valid_months(1) is True

    def test_max_months(self):
        assert is_valid_months(480) is True

    def test_zero_invalid(self):
        assert is_valid_months(0) is False

    def test_over_max(self):
        assert is_valid_months(481) is False


class TestTextSanitisation:
    def test_strips_special_chars(self):
        result = sanitise_text("Hello! World<script>")
        assert "<script>" not in result
        assert "!" not in result

    def test_max_length(self):
        long_text = "a" * 300
        result = sanitise_text(long_text, max_length=200)
        assert len(result) <= 200

    def test_preserves_alphanumeric(self):
        result = sanitise_text("Priya Sharma 123")
        assert "Priya" in result


class TestGoalInputValidation:
    def test_valid_goals(self):
        goals = [{"goal_name": "Home", "target_amount": 500000, "target_months": 36}]
        errors = validate_goal_inputs(goals)
        assert errors == []

    def test_zero_amount_error(self):
        goals = [{"goal_name": "Home", "target_amount": 0, "target_months": 36}]
        errors = validate_goal_inputs(goals)
        assert len(errors) > 0

    def test_invalid_months_error(self):
        goals = [{"goal_name": "Home", "target_amount": 500000, "target_months": 0}]
        errors = validate_goal_inputs(goals)
        assert len(errors) > 0
