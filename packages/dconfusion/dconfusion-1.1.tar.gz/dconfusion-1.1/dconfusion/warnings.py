"""
Warning system for DConfusion based on research on binary classification metrics.

This module identifies potential pitfalls in confusion matrix analysis based on
peer-reviewed research about metric reliability, sample size adequacy, and
common methodological issues in ML evaluation.

References:
- Chicco et al. on MCC advantages and ROC AUC limitations
- Lovell et al. on uncertainty in classification metrics
- Fazekas & Kovács on numerical consistency testing
"""

import math
from typing import List, Dict, Optional, Set
from enum import Enum


class WarningSeverity(Enum):
    """Severity levels for warnings."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ConfusionMatrixWarning:
    """Represents a warning about confusion matrix quality or metric reliability."""

    def __init__(self, severity: WarningSeverity, category: str, message: str,
                 recommendation: Optional[str] = None):
        """
        Initialize a confusion matrix warning.

        Args:
            severity: The severity level of the warning
            category: Category of the issue (e.g., "Sample Size", "Metric Reliability")
            message: Description of the issue
            recommendation: Optional recommendation to address the issue
        """
        self.severity = severity
        self.category = category
        self.message = message
        self.recommendation = recommendation

    def __str__(self) -> str:
        """Format warning for display."""
        result = f"[{self.severity.value}] {self.category}: {self.message}"
        if self.recommendation:
            result += f"\n  → Recommendation: {self.recommendation}"
        return result

    def __repr__(self) -> str:
        return f"ConfusionMatrixWarning(severity={self.severity}, category='{self.category}')"


class WarningChecker:
    """
    Checks confusion matrices for common pitfalls and generates warnings.

    Based on research identifying issues with:
    - Insufficient sample sizes leading to high uncertainty
    - Imbalanced classes with few samples per class
    - Metric ambiguity and interpretation issues
    - ROC AUC limitations in binary classification
    """

    # Thresholds based on research recommendations
    MIN_TOTAL_SAMPLES = 100
    MIN_SAMPLES_PER_CLASS = 30
    SEVERE_IMBALANCE_RATIO = 0.01  # 1% or less
    HIGH_UNCERTAINTY_THRESHOLD = 0.1  # 10% relative uncertainty

    def __init__(self, matrix_obj):
        """
        Initialize warning checker for a confusion matrix.

        Args:
            matrix_obj: DConfusion object to check
        """
        self.matrix = matrix_obj
        self.warnings: List[ConfusionMatrixWarning] = []

    def check_all(self) -> List[ConfusionMatrixWarning]:
        """
        Run all warning checks and return list of warnings.

        Returns:
            List of ConfusionMatrixWarning objects
        """
        self.warnings = []

        # Core data quality checks
        self._check_sample_size()
        self._check_class_balance()
        self._check_empty_cells()

        # Binary-specific checks
        if self.matrix.n_classes == 2:
            self._check_metric_uncertainty()
            self._check_perfect_classification()
            self._check_basic_rates()
            self._check_metric_ambiguity()

        return self.warnings

    def _add_warning(self, severity: WarningSeverity, category: str,
                     message: str, recommendation: Optional[str] = None):
        """Add a warning to the list."""
        warning = ConfusionMatrixWarning(severity, category, message, recommendation)
        self.warnings.append(warning)

    def _check_sample_size(self):
        """
        Check if total sample size is adequate.

        Based on Lovell et al.: uncertainty scales as 1/√N, so larger samples
        are needed for reliable metric estimates.
        """
        total = self.matrix.total

        if total == 0:
            self._add_warning(
                WarningSeverity.CRITICAL,
                "Sample Size",
                "Confusion matrix is empty (total=0).",
                "Cannot calculate any meaningful metrics with zero samples."
            )
            return

        if total < self.MIN_TOTAL_SAMPLES:
            uncertainty_factor = math.sqrt(self.MIN_TOTAL_SAMPLES / total)
            self._add_warning(
                WarningSeverity.WARNING,
                "Sample Size",
                f"Total sample size ({total}) is small. Metric uncertainty is approximately "
                f"{uncertainty_factor:.1f}x higher than with {self.MIN_TOTAL_SAMPLES} samples.",
                f"Collect {self.MIN_TOTAL_SAMPLES - total} more samples to reduce uncertainty, "
                f"or report confidence intervals with all metrics."
            )

    def _check_class_balance(self):
        """
        Check class balance and samples per class.

        Based on Lovell et al.: the problem isn't the balance ratio itself,
        but whether there are enough samples of EACH class. A 10/90 split
        with 1000 samples (100/900) is better than 50/50 with 20 samples (10/10).
        """
        if self.matrix.n_classes == 2:
            pos_samples = self.matrix.true_positive + self.matrix.false_negative
            neg_samples = self.matrix.true_negative + self.matrix.false_positive

            min_class_samples = min(pos_samples, neg_samples)
            total = self.matrix.total

            # Check absolute sample counts per class
            if min_class_samples < self.MIN_SAMPLES_PER_CLASS:
                minority_class = "positive" if pos_samples < neg_samples else "negative"
                self._add_warning(
                    WarningSeverity.WARNING,
                    "Class Imbalance",
                    f"Minority class ({minority_class}) has only {min_class_samples} samples. "
                    f"Metrics for this class will have high uncertainty.",
                    f"Collect at least {self.MIN_SAMPLES_PER_CLASS} samples of the {minority_class} "
                    f"class for reliable metric estimates."
                )

            # Check severe imbalance ratio
            if total > 0:
                min_ratio = min_class_samples / total
                if min_ratio < self.SEVERE_IMBALANCE_RATIO:
                    self._add_warning(
                        WarningSeverity.CRITICAL,
                        "Severe Class Imbalance",
                        f"Extreme class imbalance detected: minority class represents only "
                        f"{min_ratio*100:.2f}% of samples ({min_class_samples}/{total}).",
                        "Consider: (1) collecting more minority class samples, (2) using "
                        "stratified sampling, or (3) being especially cautious when interpreting "
                        "metrics like precision and F1 score."
                    )
        else:
            # Multi-class: check each class
            for i, label in enumerate(self.matrix.labels):
                class_samples = int(self.matrix.matrix[i, :].sum())
                if class_samples < self.MIN_SAMPLES_PER_CLASS:
                    self._add_warning(
                        WarningSeverity.WARNING,
                        "Class Imbalance",
                        f"Class '{label}' has only {class_samples} samples, which may lead to "
                        f"unreliable per-class metrics.",
                        f"Collect at least {self.MIN_SAMPLES_PER_CLASS} samples for class '{label}'."
                    )

    def _check_empty_cells(self):
        """Check for zero values in confusion matrix cells."""
        if self.matrix.n_classes == 2:
            # Binary case
            if self.matrix.true_positive == 0:
                self._add_warning(
                    WarningSeverity.CRITICAL,
                    "Zero True Positives",
                    "No true positives (TP=0). Precision and recall are undefined or zero.",
                    "The model failed to correctly identify any positive cases. "
                    "Check if the model is trained correctly or if the threshold is appropriate."
                )

            if self.matrix.true_negative == 0:
                self._add_warning(
                    WarningSeverity.CRITICAL,
                    "Zero True Negatives",
                    "No true negatives (TN=0). Specificity is undefined or zero.",
                    "The model failed to correctly identify any negative cases. "
                    "Check model calibration and decision threshold."
                )

            if self.matrix.false_positive == 0 and self.matrix.false_negative == 0:
                # Perfect classification - handle in separate check
                pass
            elif self.matrix.false_positive == 0:
                self._add_warning(
                    WarningSeverity.INFO,
                    "Zero False Positives",
                    "No false positives (FP=0). While this seems good, verify that the model "
                    "isn't simply predicting all negatives.",
                    "Check the distribution of predictions and consider if the model is too conservative."
                )
            elif self.matrix.false_negative == 0:
                self._add_warning(
                    WarningSeverity.INFO,
                    "Zero False Negatives",
                    "No false negatives (FN=0). While this seems good, verify that the model "
                    "isn't simply predicting all positives.",
                    "Check the distribution of predictions and consider if the model is too aggressive."
                )

    def _check_metric_uncertainty(self):
        """
        Estimate and warn about metric uncertainty.

        Based on Lovell et al.: uncertainty in metrics scales as 1/√N.
        This is a simplified estimate using binomial proportion confidence intervals.
        """
        total = self.matrix.total
        if total == 0:
            return

        # Estimate relative uncertainty for accuracy using √(p(1-p)/n)
        accuracy = self.matrix.get_accuracy()
        if total > 1:
            # Standard error for binomial proportion
            std_error = math.sqrt(accuracy * (1 - accuracy) / total)
            relative_uncertainty = std_error / accuracy if accuracy > 0 else float('inf')

            if relative_uncertainty > self.HIGH_UNCERTAINTY_THRESHOLD:
                self._add_warning(
                    WarningSeverity.WARNING,
                    "High Metric Uncertainty",
                    f"Metric uncertainty is high (±{std_error*100:.1f}% for accuracy). "
                    f"With n={total}, differences smaller than ~{std_error*2*100:.1f}% may not be meaningful.",
                    f"Need {int(4 * total)} samples to halve the uncertainty, or always report "
                    f"confidence intervals when comparing models."
                )

    def _check_perfect_classification(self):
        """Check for suspiciously perfect results."""
        if self.matrix.n_classes == 2:
            if self.matrix.false_positive == 0 and self.matrix.false_negative == 0:
                self._add_warning(
                    WarningSeverity.WARNING,
                    "Perfect Classification",
                    "Model achieved perfect classification (100% accuracy). This is rare in practice.",
                    "Verify: (1) No data leakage between train/test sets, (2) Proper cross-validation, "
                    "(3) Target variable not included as feature, (4) Test set is representative of real data. "
                    "Perfect results often indicate methodological issues."
                )

    def _check_basic_rates(self):
        """
        Check all four basic rates (TPR, TNR, PPV, NPV) as recommended by research.

        Based on Chicco et al.: high performance in one metric can mask poor performance
        in specific basic rates. All four should be examined.
        """
        if self.matrix.n_classes != 2:
            return

        try:
            tpr = self.matrix.get_recall()  # Sensitivity
            tnr = self.matrix.get_specificity()  # Specificity
            ppv = self.matrix.get_precision()  # Precision / Positive Predictive Value

            # NPV calculation
            tn = self.matrix.true_negative
            fn = self.matrix.false_negative
            npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0

            LOW_THRESHOLD = 0.7

            poor_rates = []
            if tpr < LOW_THRESHOLD:
                poor_rates.append(f"Sensitivity/Recall (TPR={tpr:.3f})")
            if tnr < LOW_THRESHOLD:
                poor_rates.append(f"Specificity (TNR={tnr:.3f})")
            if ppv < LOW_THRESHOLD:
                poor_rates.append(f"Precision (PPV={ppv:.3f})")
            if npv < LOW_THRESHOLD:
                poor_rates.append(f"Negative Predictive Value (NPV={npv:.3f})")

            if poor_rates:
                self._add_warning(
                    WarningSeverity.WARNING,
                    "Poor Basic Rates",
                    f"One or more basic rates are below {LOW_THRESHOLD}: {', '.join(poor_rates)}.",
                    "High accuracy or ROC AUC can hide poor performance in specific rates. "
                    "Consider whether these poor rates are acceptable for your application, "
                    "or if model improvement or threshold adjustment is needed."
                )
        except (ZeroDivisionError, ValueError):
            # Some metrics undefined - already warned about in empty cells check
            pass

    def _check_metric_ambiguity(self):
        """
        Warn about specific metric interpretation issues identified in research.

        Based on Chicco et al. and others:
        - ROC AUC can be high even when both sensitivity AND specificity are poor
        - Same ROC AUC can correspond to vastly different MCC values
        - Accuracy can be misleading with imbalanced classes
        """
        if self.matrix.n_classes != 2:
            return

        accuracy = self.matrix.get_accuracy()

        # Check if accuracy is misleading due to imbalance
        pos_samples = self.matrix.true_positive + self.matrix.false_negative
        neg_samples = self.matrix.true_negative + self.matrix.false_positive
        total = self.matrix.total

        if total > 0:
            majority_ratio = max(pos_samples, neg_samples) / total

            # If accuracy is close to majority class ratio, model might be trivial
            if abs(accuracy - majority_ratio) < 0.05 and majority_ratio > 0.7:
                self._add_warning(
                    WarningSeverity.WARNING,
                    "Potentially Misleading Accuracy",
                    f"Accuracy ({accuracy:.3f}) is close to the majority class proportion "
                    f"({majority_ratio:.3f}). The model may not be learning meaningful patterns.",
                    "Check if the model is simply predicting the majority class. "
                    "Consider using balanced metrics like MCC, F1 score, or balanced accuracy. "
                    "Always report all four basic rates (TPR, TNR, PPV, NPV)."
                )

        # Add general information about metric selection
        self._add_warning(
            WarningSeverity.INFO,
            "Metric Selection Guidance",
            "Different metrics emphasize different aspects of classifier performance. "
            "No single metric is 'best' for all contexts.",
            "Report multiple metrics: (1) All four basic rates (Sensitivity, Specificity, "
            "Precision, NPV), (2) A summary metric appropriate for your use case (MCC for "
            "balanced view, F1 for precision-recall tradeoff, etc.), (3) Confidence intervals "
            "or uncertainty estimates when comparing models."
        )

    def get_warnings_by_severity(self, severity: WarningSeverity) -> List[ConfusionMatrixWarning]:
        """
        Filter warnings by severity level.

        Args:
            severity: The severity level to filter by

        Returns:
            List of warnings matching the severity level
        """
        return [w for w in self.warnings if w.severity == severity]

    def has_critical_warnings(self) -> bool:
        """Check if any critical warnings exist."""
        return any(w.severity == WarningSeverity.CRITICAL for w in self.warnings)

    def format_warnings(self, include_info: bool = True) -> str:
        """
        Format all warnings as a readable string.

        Args:
            include_info: Whether to include INFO level warnings

        Returns:
            Formatted string with all warnings
        """
        if not self.warnings:
            return "No warnings detected."

        warnings_to_show = self.warnings
        if not include_info:
            warnings_to_show = [w for w in self.warnings
                              if w.severity != WarningSeverity.INFO]

        if not warnings_to_show:
            return "No warnings detected."

        result = ["\n" + "="*80]
        result.append("CONFUSION MATRIX ANALYSIS WARNINGS")
        result.append("="*80 + "\n")

        # Group by severity
        for severity in [WarningSeverity.CRITICAL, WarningSeverity.WARNING, WarningSeverity.INFO]:
            severity_warnings = [w for w in warnings_to_show if w.severity == severity]
            if severity_warnings:
                result.append(f"\n{severity.value} ({len(severity_warnings)}):")
                result.append("-" * 80)
                for warning in severity_warnings:
                    result.append(str(warning))
                    result.append("")

        result.append("="*80)
        result.append("\nFor more information on these warnings, see package documentation.")
        result.append("Based on research: Chicco et al., Lovell et al., Fazekas & Kovács.")
        result.append("="*80)

        return "\n".join(result)


def check_comparison_validity(matrix1, matrix2) -> List[ConfusionMatrixWarning]:
    """
    Check if comparing two confusion matrices is statistically meaningful.

    Based on Lovell et al.: uncertainty can eclipse differences in performance.
    Small differences between models may not be meaningful if sample sizes are small.

    Args:
        matrix1: First DConfusion object
        matrix2: Second DConfusion object

    Returns:
        List of warnings about the comparison
    """
    warnings = []

    # Check if sample sizes are similar
    if abs(matrix1.total - matrix2.total) / max(matrix1.total, matrix2.total) > 0.1:
        warnings.append(ConfusionMatrixWarning(
            WarningSeverity.WARNING,
            "Comparison: Different Sample Sizes",
            f"Models evaluated on different sample sizes ({matrix1.total} vs {matrix2.total}). "
            f"Direct comparison may be misleading.",
            "Ideally, compare models on the same test set. If not possible, use "
            "confidence intervals to account for different uncertainty levels."
        ))

    # Check if sample sizes are adequate for comparison
    min_total = min(matrix1.total, matrix2.total)
    if min_total < 100:
        warnings.append(ConfusionMatrixWarning(
            WarningSeverity.WARNING,
            "Comparison: Small Sample Size",
            f"Smallest sample size ({min_total}) is quite small for reliable comparison. "
            f"Uncertainty in metrics is high.",
            "Collect more test data before making strong conclusions about which model is better. "
            "If not possible, report confidence intervals and check if they overlap."
        ))

    # Estimate if difference is meaningful
    if matrix1.n_classes == 2 and matrix2.n_classes == 2:
        try:
            acc1 = matrix1.get_accuracy()
            acc2 = matrix2.get_accuracy()
            diff = abs(acc1 - acc2)

            # Rough estimate of standard error
            avg_total = (matrix1.total + matrix2.total) / 2
            se = math.sqrt(0.25 / avg_total)  # Conservative estimate assuming p=0.5

            if diff < 2 * se:
                warnings.append(ConfusionMatrixWarning(
                    WarningSeverity.WARNING,
                    "Comparison: Small Difference",
                    f"Accuracy difference ({diff:.4f}) is smaller than ~2 standard errors ({2*se:.4f}). "
                    f"This difference may not be statistically significant.",
                    "Perform a proper statistical test (e.g., McNemar's test for paired data, "
                    "or proportion z-test) or calculate confidence intervals to assess significance."
                ))
        except (ZeroDivisionError, ValueError):
            pass

    return warnings
