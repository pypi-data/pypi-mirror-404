"""
Validation utilities for DConfusion.

This module contains validation helper functions used throughout the package.
"""


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_non_zero_denominator(denominator: float, metric_name: str) -> None:
    """
    Helper method to validate denominators for metric calculations.

    Args:
        denominator: The denominator value to validate
        metric_name: Name of the metric being calculated

    Raises:
        ZeroDivisionError: If denominator is zero
    """
    if denominator == 0:
        raise ZeroDivisionError(f"Cannot calculate {metric_name}: denominator is zero")


def validate_binary_input(true_positive: int, false_negative: int,
                         false_positive: int, true_negative: int) -> None:
    """
    Validate binary classification inputs.

    Args:
        true_positive: Number of true positive predictions
        false_negative: Number of false negative predictions
        false_positive: Number of false positive predictions
        true_negative: Number of true negative predictions

    Raises:
        TypeError: If any input is not a number
        ValueError: If any input is negative
    """
    values = [true_positive, false_negative, false_positive, true_negative]
    names = ['true_positive', 'false_negative', 'false_positive', 'true_negative']

    for value, name in zip(values, names):
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{name} must be non-negative, got {value}")
