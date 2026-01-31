"""
Core module for DConfusion.

This module contains the base DConfusion class with initialization,
matrix management, and display methods.
"""

from typing import List, Dict, Union, Optional, Any
import numpy as np

from .validation import validate_binary_input


class DConfusionCore:
    """
    Core confusion matrix class for both binary and multi-class classification.

    This class handles the initialization and basic matrix operations.
    """

    def __init__(self, true_positive: Optional[int] = None, false_negative: Optional[int] = None,
                 false_positive: Optional[int] = None, true_negative: Optional[int] = None,
                 confusion_matrix: Optional[Union[List[List[int]], np.ndarray]] = None,
                 labels: Optional[List[Any]] = None):
        """
        Initialize DConfusion object.

        Args:
            For binary classification:
                true_positive (int): Number of true positive predictions
                false_negative (int): Number of false negative predictions
                false_positive (int): Number of false positive predictions
                true_negative (int): Number of true negative predictions

            For multi-class classification:
                confusion_matrix (List[List[int]] or np.ndarray): NxN confusion matrix
                labels (List): Optional list of class labels

        Raises:
            ValueError: If any input value is negative or matrix dimensions don't match
            TypeError: If any input value is not a number
        """
        # Determine if this is binary or multi-class based on inputs
        if confusion_matrix is not None:
            self._init_multiclass(confusion_matrix, labels)
        elif all(v is not None for v in [true_positive, false_negative, false_positive, true_negative]):
            self._init_binary(true_positive, false_negative, false_positive, true_negative)
            self._init_freq()
        else:
            raise ValueError("Either provide (tp, fn, fp, tn) for binary classification or confusion_matrix for multi-class")

    def _init_binary(self, true_positive: int, false_negative: int, false_positive: int, true_negative: int):
        """Initialize for binary classification."""
        # Input validation
        validate_binary_input(true_positive, false_negative, false_positive, true_negative)

        self.is_binary = True
        self.true_positive = int(true_positive)
        self.false_positive = int(false_positive)
        self.true_negative = int(true_negative)
        self.false_negative = int(false_negative)
        self.total = self.true_positive + self.false_negative + self.false_positive + self.true_negative

        # Create 2x2 matrix representation
        self.matrix = np.array([[self.true_positive, self.false_positive],
                               [self.false_negative, self.true_negative]])
        self.labels = [0, 1]  # Default binary labels
        self.n_classes = 2

    def _init_multiclass(self, confusion_matrix: Union[List[List[int]], np.ndarray], labels: Optional[List[Any]] = None):
        """Initialize for multi-class classification."""
        self.is_binary = False

        # Convert to numpy array
        self.matrix = np.array(confusion_matrix)

        # Validation
        if len(self.matrix.shape) != 2:
            raise ValueError("Confusion matrix must be 2-dimensional")
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Confusion matrix must be square")
        if np.any(self.matrix < 0):
            raise ValueError("All values in confusion matrix must be non-negative")

        self.n_classes = self.matrix.shape[0]
        self.total = int(np.sum(self.matrix))

        # Set labels
        if labels is None:
            self.labels = list(range(self.n_classes))
        else:
            if len(labels) != self.n_classes:
                raise ValueError(f"Number of labels ({len(labels)}) must match matrix size ({self.n_classes})")
            self.labels = list(labels)

        # For binary case, also set individual values for backward compatibility
        if self.n_classes == 2:
            self.true_positive = int(self.matrix[1, 1])
            self.false_positive = int(self.matrix[0, 1])
            self.true_negative = int(self.matrix[0, 0])
            self.false_negative = int(self.matrix[1, 0])

    def _init_freq(self):
        """
        Calculate and store frequency percentages for each cell.

        Raises:
            ZeroDivisionError: If total is zero
        """
        if self.total == 0:
            raise ZeroDivisionError("Cannot calculate frequency for an empty confusion matrix")

        if self.is_binary and self.n_classes == 2:
            self.tp_freq = (self.true_positive / self.total) * 100
            self.tn_freq = (self.true_negative / self.total) * 100
            self.fp_freq = (self.false_positive / self.total) * 100
            self.fn_freq = (self.false_negative / self.total) * 100

    def __str__(self) -> str:
        """String representation of the confusion matrix."""
        if self.is_binary and self.n_classes == 2:
            return (
                f"Confusion Matrix:\n"
                f"                 \t Predicted Positive  Predicted Negative\n"
                f"Actual Positive  \t{self.true_positive:^18}  {self.false_negative:^18}\n"
                f"Actual Negative  \t{self.false_positive:^18}  {self.true_negative:^18}"
            )
        else:
            return self._format_multiclass_matrix()

    def _format_multiclass_matrix(self) -> str:
        """Format multi-class confusion matrix for display."""
        # Calculate column widths
        max_label_width = max(len(str(label)) for label in self.labels)
        max_value_width = max(len(str(val)) for val in self.matrix.flatten())
        col_width = max(max_label_width, max_value_width, 8) + 2

        result = "Confusion Matrix:\n"

        # Header row
        result += "True\\Pred".ljust(max_label_width + 2)
        for label in self.labels:
            result += str(label).center(col_width)
        result += "\n"

        # Data rows
        for i, true_label in enumerate(self.labels):
            result += str(true_label).ljust(max_label_width + 2)
            for j in range(self.n_classes):
                result += str(self.matrix[i, j]).center(col_width)
            result += "\n"

        return result.rstrip()

    def __repr__(self) -> str:
        """Detailed representation of the DConfusion object."""
        if self.is_binary and self.n_classes == 2:
            return (f"DConfusion(true_positive={self.true_positive}, "
                    f"false_negative={self.false_negative}, "
                    f"false_positive={self.false_positive}, "
                    f"true_negative={self.true_negative})")
        else:
            return f"DConfusion(confusion_matrix={self.matrix.tolist()}, labels={self.labels})"

    def __eq__(self, other) -> bool:
        """Check equality with another DConfusion object."""
        if not isinstance(other, self.__class__.__bases__[0] if self.__class__.__bases__ else DConfusionCore):
            # Allow comparison with any class that has the same base
            if not hasattr(other, 'matrix') or not hasattr(other, 'labels'):
                return False
        return (np.array_equal(self.matrix, other.matrix) and
                self.labels == other.labels)

    def frequency(self) -> str:
        """
        Calculate and return frequency percentages for each cell.

        Returns:
            str: Formatted string showing frequency percentages

        Raises:
            ZeroDivisionError: If total is zero
        """
        if self.total == 0:
            raise ZeroDivisionError("Cannot calculate frequency for an empty confusion matrix")

        if self.is_binary and self.n_classes == 2:
            return (
                f"Confusion Matrix Frequency (%):\n"
                f"                 \t Predicted Positive  Predicted Negative\n"
                f"Actual Positive  \t{self.tp_freq:^18.2f}  {self.fn_freq:^18.2f}\n"
                f"Actual Negative  \t{self.fp_freq:^18.2f}  {self.tn_freq:^18.2f}"
            )
        else:
            return self._format_multiclass_frequency()

    def _format_multiclass_frequency(self) -> str:
        """Format multi-class frequency matrix for display."""
        freq_matrix = (self.matrix / self.total) * 100

        max_label_width = max(len(str(label)) for label in self.labels)
        col_width = 10

        result = "Confusion Matrix Frequency (%):\n"

        # Header row
        result += "True\\Pred".ljust(max_label_width + 2)
        for label in self.labels:
            result += str(label).center(col_width)
        result += "\n"

        # Data rows
        for i, true_label in enumerate(self.labels):
            result += str(true_label).ljust(max_label_width + 2)
            for j in range(self.n_classes):
                result += f"{freq_matrix[i, j]:.2f}".center(col_width)
            result += "\n"

        return result.rstrip()

    def validate_matrix(self) -> bool:
        """
        Validate that the confusion matrix is internally consistent.

        Returns:
            bool: True if matrix is valid

        Raises:
            ValueError: If matrix contains inconsistencies
        """
        if np.any(self.matrix < 0):
            raise ValueError("Confusion matrix cannot contain negative values")

        if self.total != np.sum(self.matrix):
            raise ValueError("Matrix total doesn't match sum of all cells")
        # TODO: Planning to add more validations here in upcoming versions
        return True

    def check_warnings(self, include_info: bool = True):
        """
        Check for potential issues and pitfalls in the confusion matrix.

        This method analyzes the confusion matrix for common problems identified
        in research on binary classification metrics, including:
        - Insufficient sample sizes
        - Class imbalance issues
        - High metric uncertainty
        - Potentially misleading metrics

        Args:
            include_info: Whether to include informational warnings (default: True)

        Returns:
            List of ConfusionMatrixWarning objects

        Example:
            >>> cm = DConfusion(tp=10, fn=5, fp=3, tn=12)
            >>> warnings = cm.check_warnings()
            >>> for w in warnings:
            ...     print(w)
        """
        from .warnings import WarningChecker
        checker = WarningChecker(self)
        return checker.check_all()

    def print_warnings(self, include_info: bool = True):
        """
        Print formatted warnings about potential issues in the confusion matrix.

        Args:
            include_info: Whether to include informational warnings (default: True)

        Example:
            >>> cm = DConfusion(tp=10, fn=5, fp=3, tn=12)
            >>> cm.print_warnings()
        """
        from .warnings import WarningChecker
        checker = WarningChecker(self)
        checker.check_all()
        print(checker.format_warnings(include_info=include_info))
