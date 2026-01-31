"""
DConfusion - A comprehensive confusion matrix class.

This module maintains backwards compatibility by importing all functionality
from the refactored submodules.
"""

from .core import DConfusionCore
from .metrics import MetricsMixin
from .visualization import VisualizationMixin
from .io import IOMixin
from .statistics import StatisticalTestsMixin, MetricInferenceMixin

# ConsistencyMixin is optional - requires mlscorecheck
try:
    from .consistency import ConsistencyMixin
    _HAS_CONSISTENCY = True
except ImportError:
    _HAS_CONSISTENCY = False
    # Create a stub mixin that provides helpful error messages
    class ConsistencyMixin:
        """Stub mixin when mlscorecheck is not installed."""
        def check_reported_scores(self, *args, **kwargs):
            raise ImportError(
                "Consistency testing requires 'mlscorecheck'. "
                "Install with: pip install mlscorecheck "
                "or pip install dconfusion[consistency]"
            )
        def verify_own_scores(self, *args, **kwargs):
            raise ImportError(
                "Consistency testing requires 'mlscorecheck'. "
                "Install with: pip install mlscorecheck "
                "or pip install dconfusion[consistency]"
            )


class DConfusion(DConfusionCore, MetricsMixin, VisualizationMixin, IOMixin,
                  StatisticalTestsMixin, MetricInferenceMixin, ConsistencyMixin):
    """
    A comprehensive confusion matrix class for both binary and multi-class classification analysis.

    This class can handle:
    1. Binary classification using individual TP, FN, FP, TN values
    2. Multi-class classification using a confusion matrix or predictions

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
    pass