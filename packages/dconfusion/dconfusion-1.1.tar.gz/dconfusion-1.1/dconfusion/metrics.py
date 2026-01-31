"""
Metrics calculation module for DConfusion.

This module contains all metric calculation methods for confusion matrices,
including both binary and multi-class metrics.
"""

import math
from typing import Dict, Any, Optional, Tuple
import numpy as np

from .validation import validate_non_zero_denominator


class MetricsMixin:
    """Mixin class providing metric calculation methods for confusion matrices."""

    def get_sum_of_all(self) -> int:
        """Get total number of samples."""
        return self.total

    def get_confusion_matrix(self) -> list:
        """
        Get confusion matrix as a 2D list.

        Returns:
            List[List[int]]: NxN matrix
        """
        return self.matrix.tolist()

    def get_sum_of_errors(self) -> int:
        """
        Get total number of incorrect predictions.

        Returns:
            int: Number of samples that were classified incorrectly
        """
        return self.total - int(np.trace(self.matrix))

    def get_sum_of_corrects(self) -> int:
        """
        Get total number of correct predictions.

        Returns:
            int: Number of samples that were classified correctly
        """
        return int(np.trace(self.matrix))

    def get_accuracy(self) -> float:
        """
        Calculate overall accuracy.

        Returns:
            float: Accuracy value between 0 and 1
        """
        validate_non_zero_denominator(self.total, "accuracy")
        return np.trace(self.matrix) / self.total

    def get_expected_accuracy(self) -> float:
        """
        Calculate expected accuracy (chance agreement) for Cohen's Kappa calculation.

        Expected accuracy is the accuracy that would be achieved by chance alone,
        calculated as the sum of the products of marginal probabilities.

        Returns:
            float: Expected accuracy value between 0 and 1

        Raises:
            ValueError: If not binary classification (only supports 2x2 matrices)
        """
        if self.n_classes != 2:
            raise ValueError("Expected accuracy is only available for binary classification")
        return ((((self.true_positive + self.false_positive)/self.total)*(self.true_positive + self.false_negative)/self.total)
                + (((self.true_negative + self.false_positive)/self.total)*(self.true_negative + self.false_negative)/self.total))

    # Alias for accuracy
    get_ccr = get_accuracy

    def get_error_rate(self) -> float:
        """
        Calculate overall error rate (1 - accuracy).

        Returns:
            float: Error rate value between 0 and 1
        """
        return 1 - self.get_accuracy()

    def get_class_metrics(self, class_index: Optional[int] = None, class_label: Optional[Any] = None) -> Dict[str, float]:
        """
        Get metrics for a specific class in multi-class setting.

        Args:
            class_index: Index of the class (0-based)
            class_label: Label of the class

        Returns:
            Dict with precision, recall, f1_score, specificity for the class
        """
        if class_label is not None:
            if class_label not in self.labels:
                raise ValueError(f"Class label '{class_label}' not found in {self.labels}")
            class_index = self.labels.index(class_label)
        elif class_index is None:
            raise ValueError("Either class_index or class_label must be provided")

        if not 0 <= class_index < self.n_classes:
            raise ValueError(f"class_index must be between 0 and {self.n_classes-1}")

        # Calculate TP, FP, FN, TN for this class
        tp = self.matrix[class_index, class_index]
        fp = np.sum(self.matrix[:, class_index]) - tp
        fn = np.sum(self.matrix[class_index, :]) - tp
        tn = self.total - tp - fp - fn

        metrics = {}

        # Precision
        try:
            metrics['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        except:
            metrics['precision'] = 0.0

        # Recall
        try:
            metrics['recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        except:
            metrics['recall'] = 0.0

        # F1 Score
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = 2 * metrics['precision'] * metrics['recall'] / (metrics['precision'] + metrics['recall'])
        else:
            metrics['f1_score'] = 0.0

        # Specificity
        try:
            metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        except:
            metrics['specificity'] = 0.0

        return metrics

    def get_macro_metrics(self) -> Dict[str, float]:
        """Calculate macro-averaged metrics across all classes."""
        all_metrics = []

        for i in range(self.n_classes):
            class_metrics = self.get_class_metrics(class_index=i)
            all_metrics.append(class_metrics)

        # Calculate macro averages
        macro_metrics = {}
        for metric in ['precision', 'recall', 'f1_score', 'specificity']:
            values = [m[metric] for m in all_metrics if not math.isnan(m[metric])]
            macro_metrics[f'macro_{metric}'] = sum(values) / len(values) if values else 0.0

        return macro_metrics

    def get_weighted_metrics(self) -> Dict[str, float]:
        """Calculate weighted-averaged metrics across all classes."""
        all_metrics = []
        class_support = []

        for i in range(self.n_classes):
            class_metrics = self.get_class_metrics(class_index=i)
            all_metrics.append(class_metrics)
            # Support is the number of true instances for this class
            class_support.append(np.sum(self.matrix[i, :]))

        # Calculate weighted averages
        weighted_metrics = {}
        total_support = sum(class_support)

        for metric in ['precision', 'recall', 'f1_score', 'specificity']:
            weighted_sum = sum(m[metric] * support for m, support in zip(all_metrics, class_support)
                             if not math.isnan(m[metric]))
            weighted_metrics[f'weighted_{metric}'] = weighted_sum / total_support if total_support > 0 else 0.0

        return weighted_metrics

    def get_binary_values(self) -> Dict[str, int]:
        """
        Get the four basic confusion matrix values for binary classification.

        Returns:
            Dict[str, int]: Dictionary with keys 'TP', 'FN', 'FP', 'TN'

        Raises:
            ValueError: If not binary classification
        """
        if self.n_classes != 2:
            raise ValueError("Binary values are only available for binary classification")

        return {
            'TP': self.true_positive,
            'FN': self.false_negative,
            'FP': self.false_positive,
            'TN': self.true_negative
        }

    # Binary classification methods (work for binary case or when n_classes=2)
    def get_recall(self) -> float:
        """Calculate recall for binary classification or positive class."""
        if not hasattr(self, 'true_positive'):
            # Use class 1 (positive class) for multi-class
            return self.get_class_metrics(class_index=1)['recall']

        denominator = self.true_positive + self.false_negative
        validate_non_zero_denominator(denominator, "recall")
        return self.true_positive / denominator

    def get_precision(self) -> float:
        """Calculate precision for binary classification or positive class."""
        if not hasattr(self, 'true_positive'):
            # Use class 1 (positive class) for multi-class
            return self.get_class_metrics(class_index=1)['precision']

        denominator = self.true_positive + self.false_positive
        validate_non_zero_denominator(denominator, "precision")
        return self.true_positive / denominator

    def get_f1_score(self) -> float:
        """Calculate F1 score for binary classification or positive class."""
        if not hasattr(self, 'true_positive'):
            # Use class 1 (positive class) for multi-class
            return self.get_class_metrics(class_index=1)['f1_score']

        precision = self.get_precision()
        recall = self.get_recall()
        denominator = precision + recall
        validate_non_zero_denominator(denominator, "F1 score")
        return 2 * precision * recall / denominator

    def get_specificity(self) -> float:
        """Calculate specificity for binary classification or negative class."""
        if not hasattr(self, 'true_negative'):
            # Use class 0 (negative class) for multi-class
            return self.get_class_metrics(class_index=0)['specificity']

        denominator = self.true_negative + self.false_positive
        validate_non_zero_denominator(denominator, "specificity")
        return self.true_negative / denominator

    # Aliases for backward compatibility
    get_true_positive_rate = get_recall
    get_sensitivity = get_recall
    get_probability_of_detection = get_recall
    get_true_negative_rate = get_specificity
    get_f_measure = get_f1_score

    def get_false_positive_rate(self) -> float:
        """
        Calculate false positive rate (Type I error rate).

        Also known as fall-out or probability of false alarm.
        FPR = FP / (FP + TN)

        Returns:
            float: False positive rate value between 0 and 1
        """
        if not hasattr(self, 'false_positive'):
            # Calculate for positive class in multi-class
            class_metrics = self.get_class_metrics(class_index=1)
            return 1 - class_metrics['specificity']

        denominator = self.false_positive + self.true_negative
        validate_non_zero_denominator(denominator, "false positive rate")
        return self.false_positive / denominator

    def get_false_negative_rate(self) -> float:
        """
        Calculate false negative rate (Type II error rate).

        Also known as miss rate.
        FNR = FN / (FN + TP) = 1 - Recall

        Returns:
            float: False negative rate value between 0 and 1
        """
        return 1 - self.get_recall()

    # More aliases
    get_type_1_error = get_false_positive_rate
    get_probability_of_false_alarm = get_false_positive_rate
    get_type_2_error = get_false_negative_rate

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available metrics."""
        metrics = {
            'accuracy': self.get_accuracy(),
            'error_rate': self.get_error_rate(),
        }

        if self.n_classes == 2:
            # Binary metrics
            try:
                metrics.update({
                    'expected_accuracy': self.get_expected_accuracy(),
                    'precision': self.get_precision(),
                    'recall': self.get_recall(),
                    'specificity': self.get_specificity(),
                    'f1_score': self.get_f1_score(),
                    'false_positive_rate': self.get_false_positive_rate(),
                    'false_negative_rate': self.get_false_negative_rate(),
                    'false_omission_rate': self.get_false_omission_rate(),
                    'false_discovery_rate': self.get_false_discovery_rate(),
                })

                if hasattr(self, 'get_g_mean'):
                    metrics['g_mean'] = self.get_g_mean()
                if hasattr(self, 'get_balance'):
                    metrics['balance'] = self.get_balance()
                if hasattr(self, 'get_matthews_correlation_coefficient'):
                    metrics['matthews_correlation_coefficient'] = self.get_matthews_correlation_coefficient()
                if hasattr(self, 'get_cohens_kappa'):
                    metrics['cohens_kappa'] = self.get_cohens_kappa()
                if hasattr(self, 'brier_score'):
                    metrics['brier_score'] = self.brier_score()

            except ZeroDivisionError as e:
                metrics['error'] = str(e)
        else:
            # Multi-class metrics
            metrics.update(self.get_macro_metrics())
            metrics.update(self.get_weighted_metrics())

            # Per-class metrics
            metrics['per_class_metrics'] = {}
            for i, label in enumerate(self.labels):
                try:
                    metrics['per_class_metrics'][str(label)] = self.get_class_metrics(class_index=i)
                except:
                    pass

        return metrics

    # Keep existing binary-specific methods for backward compatibility
    def get_g_mean(self) -> float:
        """Calculate geometric mean (binary only)."""
        if self.n_classes != 2:
            raise ValueError("G-mean is only available for binary classification")
        return math.sqrt(self.get_precision() * self.get_recall())

    def get_balance(self) -> float:
        """Calculate balance metric (binary only)."""
        if self.n_classes != 2:
            raise ValueError("Balance is only available for binary classification")
        fpr = self.get_false_positive_rate()
        tpr = self.get_recall()
        return 1 - (math.sqrt((0 - fpr)**2 + (1 - tpr)**2)) / math.sqrt(2)

    def get_matthews_correlation_coefficient(self) -> float:
        """Calculate Matthews Correlation Coefficient (binary only)."""
        if self.n_classes != 2:
            raise ValueError("MCC is only available for binary classification")

        numerator = (self.true_positive * self.true_negative -
                    self.false_positive * self.false_negative)

        denominator = math.sqrt(
            (self.true_positive + self.false_positive) *
            (self.true_positive + self.false_negative) *
            (self.true_negative + self.false_positive) *
            (self.true_negative + self.false_negative)
        )

        validate_non_zero_denominator(denominator, "Matthews Correlation Coefficient")
        return numerator / denominator

    def get_cohens_kappa(self) -> float:
        """
        Calculate Cohen's kappa coefficient (binary only).

        Cohen's kappa measures inter-rater agreement for categorical items,
        accounting for chance agreement. Ranges from -1 to 1, where:
        - 1 indicates perfect agreement
        - 0 indicates agreement by chance alone
        - Negative values indicate agreement worse than chance

        Formula: κ = (Observed Agreement - Expected Agreement) / (1 - Expected Agreement)

        Returns:
            float: Cohen's kappa coefficient

        Raises:
            ValueError: If not binary classification
        """
        if self.n_classes != 2:
            raise ValueError("Cohen's Kappa is only available for binary classification")
        cohens_kappa = (2 * (self.true_positive * self.true_negative - self.false_positive * self.false_negative)) / \
            ((self.true_positive + self.false_positive) * (self.false_positive + self.true_negative) +
             (self.true_positive + self.false_negative)*(self.false_negative + self.true_negative))
        assert(math.isclose(cohens_kappa,
                           (self.get_accuracy() - self.get_expected_accuracy()) / (1 - self.get_expected_accuracy())
                           )
              )
        return cohens_kappa

    def brier_score(self) -> float:
        """
        Calculate Brier score (binary only).

        The Brier score is a proper scoring rule that measures the accuracy
        of probabilistic predictions. For a confusion matrix, it equals 1 - accuracy.
        Lower values indicate better predictions.

        Returns:
            float: Brier score value between 0 and 1

        Raises:
            ValueError: If not binary classification
        """
        if self.n_classes != 2:
            raise ValueError("Brier score is only available for binary classification")
        brier_score = (self.false_positive + self.false_negative) / self.total
        assert math.isclose(brier_score, (1 - self.get_accuracy()))
        return brier_score

    def false_rate(self) -> float:
        """
        Calculate false rate (same as error rate).

        This is an alias for get_error_rate().

        Returns:
            float: False rate value between 0 and 1
        """
        return self.get_error_rate()

    def frequency_of_faulty_items(self) -> float:
        """
        Calculate frequency of faulty items as percentage (binary only).

        Returns the percentage of actual positive cases in the dataset.
        This represents the prevalence of the positive class.

        Returns:
            float: Percentage of positive cases (0-100)

        Raises:
            ValueError: If not binary classification
        """
        if self.n_classes != 2:
            raise ValueError("Frequency of faulty items is only available for binary classification")
        return (self.true_positive + self.false_negative) * 100 / self.total

    def get_metric_confidence_interval(self, metric: str, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for a given metric using Wilson score interval.

        Args:
            metric: Name of the metric ('accuracy', 'precision', 'recall', etc.)
            confidence: Confidence level (default 0.95 for 95% CI)

        Returns:
            Tuple: (lower_bound, upper_bound)
        """
        if metric not in ['accuracy', 'precision', 'recall', 'specificity']:
            raise ValueError(f"Confidence intervals not supported for metric: {metric}")

        # Get the metric value and sample size
        if metric == 'accuracy':
            successes = self.get_sum_of_corrects()
            n = self.total
        elif metric == 'precision':
            successes = self.true_positive
            n = self.true_positive + self.false_positive
        elif metric == 'recall':
            successes = self.true_positive
            n = self.true_positive + self.false_negative
        elif metric == 'specificity':
            successes = self.true_negative
            n = self.true_negative + self.false_positive

        if n == 0:
            return (0.0, 0.0)

        # Wilson score interval
        from scipy import stats
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        p = successes / n

        denominator = 1 + z ** 2 / n
        center = (p + z ** 2 / (2 * n)) / denominator
        margin = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denominator

        return max(0, center - margin), min(1, center + margin)

    def get_optimal_threshold_info(self) -> Dict[str, float]:
        """
        Calculate metrics related to optimal threshold selection (binary only).

        Returns:
            Dict: Information about current operating point
        """
        if self.n_classes != 2:
            raise ValueError("Threshold analysis only available for binary classification")

        tpr = self.get_recall()
        fpr = self.get_false_positive_rate()

        return {
            'sensitivity': tpr,
            'specificity': 1 - fpr,
            'youden_index': tpr + (1 - fpr) - 1,  # J = Sensitivity + Specificity - 1
            'distance_to_perfect': math.sqrt((1 - tpr) ** 2 + fpr ** 2),
            'likelihood_ratio_positive': tpr / fpr if fpr > 0 else float('inf'),
            'likelihood_ratio_negative': (1 - tpr) / (1 - fpr) if fpr < 1 else float('inf')
        }

    @property
    def accuracy(self) -> float:
        """Accuracy property for convenient access."""
        return self.get_accuracy()

    @property
    def precision(self) -> float:
        """Precision property for convenient access."""
        return self.get_precision()

    @property
    def recall(self) -> float:
        """Recall property for convenient access."""
        return self.get_recall()

    @property
    def f1_score(self) -> float:
        """F1 score property for convenient access."""
        return self.get_f1_score()

    @property
    def specificity(self) -> float:
        """Specificity property for convenient access."""
        return self.get_specificity()

    def compare_with(self, other, metric: str = 'accuracy', show_warnings: bool = True) -> Dict[str, Any]:
        """
        Compare this confusion matrix with another.

        Args:
            other: Another DConfusion object to compare with
            metric: Metric to compare (default: 'accuracy')
            show_warnings: Whether to check and return warnings about comparison validity

        Returns:
            Dict containing comparison results and optional warnings

        Example:
            >>> cm1 = DConfusion(tp=50, fn=10, fp=5, tn=35)
            >>> cm2 = DConfusion(tp=45, fn=15, fp=8, tn=32)
            >>> result = cm1.compare_with(cm2)
            >>> print(result['difference'])
        """
        from .warnings import check_comparison_validity

        # Get metric values
        metric_getter = f'get_{metric}'
        if not hasattr(self, metric_getter):
            raise ValueError(f"Unknown metric: {metric}")

        value1 = getattr(self, metric_getter)()
        value2 = getattr(other, metric_getter)()

        result = {
            'metric': metric,
            'value1': value1,
            'value2': value2,
            'difference': value1 - value2,
            'relative_difference': (value1 - value2) / value2 if value2 != 0 else float('inf'),
            'better_model': 'model1' if value1 > value2 else 'model2' if value2 > value1 else 'tie'
        }

        if show_warnings:
            warnings = check_comparison_validity(self, other)
            result['warnings'] = warnings
            result['has_warnings'] = len(warnings) > 0

        return result

    def get_misclassification_cost(self, cost_fp: float = 1.0, cost_fn: float = 1.0,
                                   cost_tp: float = 0.0, cost_tn: float = 0.0) -> float:
        """
        Calculate total misclassification cost based on custom costs for each outcome.

        Args:
            cost_fp: Cost of false positive (default: 1.0)
            cost_fn: Cost of false negative (default: 1.0)
            cost_tp: Cost/benefit of true positive (default: 0.0, negative values indicate benefit)
            cost_tn: Cost/benefit of true negative (default: 0.0, negative values indicate benefit)

        Returns:
            float: Total cost (lower is better)

        Example:
            >>> cm = DConfusion(tp=80, fn=20, fp=10, tn=90)
            >>> # FN costs 10x more than FP (e.g., missing a disease diagnosis)
            >>> total_cost = cm.get_misclassification_cost(cost_fp=1, cost_fn=10)
        """
        if self.n_classes != 2:
            raise ValueError("Cost-sensitive analysis is only available for binary classification")

        total_cost = (cost_tp * self.true_positive +
                     cost_tn * self.true_negative +
                     cost_fp * self.false_positive +
                     cost_fn * self.false_negative)

        return total_cost

    def get_average_misclassification_cost(self, cost_fp: float = 1.0, cost_fn: float = 1.0,
                                           cost_tp: float = 0.0, cost_tn: float = 0.0) -> float:
        """
        Calculate average misclassification cost per sample.

        Args:
            cost_fp: Cost of false positive (default: 1.0)
            cost_fn: Cost of false negative (default: 1.0)
            cost_tp: Cost/benefit of true positive (default: 0.0)
            cost_tn: Cost/benefit of true negative (default: 0.0)

        Returns:
            float: Average cost per sample

        Example:
            >>> cm = DConfusion(tp=80, fn=20, fp=10, tn=90)
            >>> avg_cost = cm.get_average_misclassification_cost(cost_fp=1, cost_fn=10)
        """
        if self.n_classes != 2:
            raise ValueError("Cost-sensitive analysis is only available for binary classification")

        validate_non_zero_denominator(self.total, "average misclassification cost")
        total_cost = self.get_misclassification_cost(cost_fp, cost_fn, cost_tp, cost_tn)
        return total_cost / self.total

    def get_cost_benefit_summary(self, cost_fp: float = 1.0, cost_fn: float = 1.0,
                                 cost_tp: float = 0.0, cost_tn: float = 0.0,
                                 benefit_tp: Optional[float] = None,
                                 benefit_tn: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate comprehensive cost-benefit analysis.

        Args:
            cost_fp: Cost of false positive (default: 1.0)
            cost_fn: Cost of false negative (default: 1.0)
            cost_tp: Cost of true positive (default: 0.0), use negative for benefit
            cost_tn: Cost of true negative (default: 0.0), use negative for benefit
            benefit_tp: Benefit of true positive (alternative to negative cost_tp)
            benefit_tn: Benefit of true negative (alternative to negative cost_tn)

        Returns:
            Dict containing detailed cost-benefit breakdown

        Example:
            >>> cm = DConfusion(tp=80, fn=20, fp=10, tn=90)
            >>> summary = cm.get_cost_benefit_summary(
            ...     cost_fp=100,  # $100 cost for false alarm
            ...     cost_fn=1000, # $1000 cost for missed detection
            ...     benefit_tp=50, # $50 benefit for correct detection
            ...     benefit_tn=10  # $10 benefit for correct rejection
            ... )
        """
        if self.n_classes != 2:
            raise ValueError("Cost-sensitive analysis is only available for binary classification")

        # Convert benefits to negative costs if provided
        if benefit_tp is not None:
            cost_tp = -benefit_tp
        if benefit_tn is not None:
            cost_tn = -benefit_tn

        total_cost = self.get_misclassification_cost(cost_fp, cost_fn, cost_tp, cost_tn)
        avg_cost = total_cost / self.total

        # Calculate individual components
        tp_component = cost_tp * self.true_positive
        tn_component = cost_tn * self.true_negative
        fp_component = cost_fp * self.false_positive
        fn_component = cost_fn * self.false_negative

        # Calculate what a perfect classifier would achieve
        perfect_cost = (cost_tp * (self.true_positive + self.false_negative) +
                       cost_tn * (self.true_negative + self.false_positive))

        # Calculate what always predicting positive would cost
        all_positive_cost = (cost_tp * (self.true_positive + self.false_negative) +
                            cost_fp * (self.false_positive + self.true_negative))

        # Calculate what always predicting negative would cost
        all_negative_cost = (cost_fn * (self.true_positive + self.false_negative) +
                            cost_tn * (self.false_positive + self.true_negative))

        # Calculate what random guessing would cost (assuming 50/50 split)
        random_cost = (cost_tp * (self.true_positive + self.false_negative) / 2 +
                      cost_fp * (self.false_positive + self.true_negative) / 2 +
                      cost_fn * (self.true_positive + self.false_negative) / 2 +
                      cost_tn * (self.false_positive + self.true_negative) / 2)

        return {
            'total_cost': total_cost,
            'average_cost': avg_cost,
            'tp_component': tp_component,
            'tn_component': tn_component,
            'fp_component': fp_component,
            'fn_component': fn_component,
            'perfect_classifier_cost': perfect_cost,
            'all_positive_cost': all_positive_cost,
            'all_negative_cost': all_negative_cost,
            'random_classifier_cost': random_cost,
            'savings_vs_perfect': total_cost - perfect_cost,
            'savings_vs_all_positive': all_positive_cost - total_cost,
            'savings_vs_all_negative': all_negative_cost - total_cost,
            'savings_vs_random': random_cost - total_cost,
            'cost_improvement_over_random': (random_cost - total_cost) / abs(random_cost) if random_cost != 0 else 0
        }

    def find_optimal_metric_for_cost(self, cost_fp: float = 1.0, cost_fn: float = 1.0) -> Dict[str, Any]:
        """
        Determine which standard metric best aligns with your cost structure.

        This method analyzes your cost ratio and recommends which metric to optimize
        for your specific use case.

        Args:
            cost_fp: Cost of false positive (default: 1.0)
            cost_fn: Cost of false negative (default: 1.0)

        Returns:
            Dict containing recommended metrics and analysis

        Example:
            >>> cm = DConfusion(tp=80, fn=20, fp=10, tn=90)
            >>> # When FN is very costly (e.g., medical diagnosis)
            >>> rec = cm.find_optimal_metric_for_cost(cost_fp=1, cost_fn=10)
            >>> print(rec['primary_recommendation'])
            'recall'
        """
        if self.n_classes != 2:
            raise ValueError("Cost-sensitive analysis is only available for binary classification")

        cost_ratio = cost_fn / cost_fp if cost_fp != 0 else float('inf')

        # Determine recommendations based on cost ratio
        if cost_ratio > 5:
            primary_metric = 'recall'
            explanation = (f"False negatives are {cost_ratio:.1f}x more costly than false positives. "
                         "Prioritize RECALL (sensitivity) to minimize missed positive cases.")
            secondary_metrics = ['f2_score', 'specificity']
        elif cost_ratio < 0.2:
            primary_metric = 'precision'
            explanation = (f"False positives are {1/cost_ratio:.1f}x more costly than false negatives. "
                         "Prioritize PRECISION to minimize false alarms.")
            secondary_metrics = ['specificity', 'f1_score']
        elif 0.5 <= cost_ratio <= 2:
            primary_metric = 'f1_score'
            explanation = (f"Costs are relatively balanced (FN/FP ratio: {cost_ratio:.2f}). "
                         "F1 score provides balanced optimization.")
            secondary_metrics = ['matthews_correlation_coefficient', 'accuracy']
        else:
            primary_metric = 'f1_score'
            explanation = (f"Cost ratio is {cost_ratio:.2f}. F1 score is recommended, but consider "
                         f"{'recall' if cost_ratio > 1 else 'precision'} as secondary metric.")
            secondary_metrics = ['recall' if cost_ratio > 1 else 'precision', 'matthews_correlation_coefficient']

        # Calculate current metric values
        current_values = {}
        for metric in [primary_metric] + secondary_metrics:
            try:
                getter = f'get_{metric}'
                if hasattr(self, getter):
                    current_values[metric] = getattr(self, getter)()
            except:
                pass

        # Calculate cost-weighted F-beta score
        if cost_ratio != 0:
            beta = math.sqrt(cost_ratio)
            precision = self.get_precision()
            recall = self.get_recall()
            denominator = (beta ** 2 * precision) + recall
            if denominator > 0:
                f_beta = (1 + beta ** 2) * precision * recall / denominator
            else:
                f_beta = 0.0
        else:
            f_beta = self.get_precision()

        return {
            'cost_ratio_fn_to_fp': cost_ratio,
            'primary_recommendation': primary_metric,
            'secondary_recommendations': secondary_metrics,
            'explanation': explanation,
            'current_metric_values': current_values,
            'cost_weighted_f_beta': f_beta,
            'beta_value': math.sqrt(cost_ratio) if cost_ratio != 0 else 0,
            'interpretation': self._interpret_cost_ratio(cost_ratio)
        }

    def _interpret_cost_ratio(self, cost_ratio: float) -> str:
        """Helper method to interpret cost ratios."""
        if cost_ratio > 10:
            return "Extremely high cost for false negatives - typical in critical medical diagnoses, safety systems"
        elif cost_ratio > 5:
            return "High cost for false negatives - typical in fraud detection, disease screening"
        elif cost_ratio > 2:
            return "Moderate preference for avoiding false negatives"
        elif 0.5 <= cost_ratio <= 2:
            return "Balanced costs - both error types matter equally"
        elif cost_ratio > 0.1:
            return "Moderate preference for avoiding false positives"
        elif cost_ratio > 0.01:
            return "High cost for false positives - typical in spam detection, marketing campaigns"
        else:
            return "Extremely high cost for false positives - false alarms are very expensive"

    def compare_cost_with(self, other, cost_fp: float = 1.0, cost_fn: float = 1.0,
                          cost_tp: float = 0.0, cost_tn: float = 0.0) -> Dict[str, Any]:
        """
        Compare the cost-effectiveness of two models based on custom cost structure.

        Args:
            other: Another DConfusion object to compare with
            cost_fp: Cost of false positive (default: 1.0)
            cost_fn: Cost of false negative (default: 1.0)
            cost_tp: Cost/benefit of true positive (default: 0.0)
            cost_tn: Cost/benefit of true negative (default: 0.0)

        Returns:
            Dict containing detailed cost comparison

        Example:
            >>> model_a = DConfusion(tp=80, fn=20, fp=10, tn=90)
            >>> model_b = DConfusion(tp=85, fn=15, fp=20, tn=80)
            >>> comparison = model_a.compare_cost_with(
            ...     model_b,
            ...     cost_fp=100,
            ...     cost_fn=1000
            ... )
            >>> print(f"Model A saves ${comparison['cost_savings']:.2f}")
        """
        if self.n_classes != 2 or other.n_classes != 2:
            raise ValueError("Cost-sensitive comparison is only available for binary classification")

        cost1 = self.get_misclassification_cost(cost_fp, cost_fn, cost_tp, cost_tn)
        cost2 = other.get_misclassification_cost(cost_fp, cost_fn, cost_tp, cost_tn)

        avg_cost1 = cost1 / self.total if self.total > 0 else 0
        avg_cost2 = cost2 / other.total if other.total > 0 else 0

        # Calculate cost savings
        cost_savings = cost2 - cost1
        relative_savings = cost_savings / abs(cost2) if cost2 != 0 else 0

        # Determine better model
        if cost1 < cost2:
            better_model = 'model1'
            recommendation = "Model 1 is more cost-effective"
        elif cost2 < cost1:
            better_model = 'model2'
            recommendation = "Model 2 is more cost-effective"
        else:
            better_model = 'tie'
            recommendation = "Both models have equal cost"

        return {
            'model1_total_cost': cost1,
            'model2_total_cost': cost2,
            'model1_average_cost': avg_cost1,
            'model2_average_cost': avg_cost2,
            'cost_difference': cost1 - cost2,
            'cost_savings': cost_savings,
            'relative_savings_percent': relative_savings * 100,
            'better_model': better_model,
            'recommendation': recommendation,
            'cost_structure': {
                'cost_fp': cost_fp,
                'cost_fn': cost_fn,
                'cost_tp': cost_tp,
                'cost_tn': cost_tn,
                'cost_ratio_fn_to_fp': cost_fn / cost_fp if cost_fp != 0 else float('inf')
            }
        }

    # =========================================================================
    # Method Aliases - Common Abbreviations
    # =========================================================================

    def get_mcc(self) -> float:
        """
        Alias for get_matthews_correlation_coefficient().

        Matthews Correlation Coefficient (MCC) is a balanced metric for binary
        classification that takes into account all four values in the confusion matrix.

        Returns:
            float: MCC value between -1 and 1
        """
        return self.get_matthews_correlation_coefficient()

    def get_npv(self) -> float:
        """
        Calculate Negative Predictive Value (NPV).

        NPV = TN / (TN + FN)

        Represents the probability that a negative prediction is correct.
        Complement of False Discovery Rate for negative predictions.

        Returns:
            float: NPV value between 0 and 1

        Raises:
            ValueError: If not binary classification
            ZeroDivisionError: If no actual negatives (TN + FN = 0)
        """
        if self.n_classes != 2:
            raise ValueError("NPV is only available for binary classification")

        from .validation import validate_non_zero_denominator
        denominator = self.true_negative + self.false_negative
        validate_non_zero_denominator(denominator, "Negative Predictive Value (NPV)")

        return self.true_negative / denominator

    def get_false_omission_rate(self) -> float:
        """
        Calculate False Omission Rate (FOR).

        FOR = FN / (TN + FN) = 1 - NPV

        Represents the probability that a negative prediction is incorrect
        (i.e., the sample is actually positive when predicted negative).

        Returns:
            float: FOR value between 0 and 1

        Raises:
            ValueError: If not binary classification
            ZeroDivisionError: If no predicted negatives (TN + FN = 0)
        """
        if self.n_classes != 2:
            raise ValueError("FOR is only available for binary classification")

        from .validation import validate_non_zero_denominator
        denominator = self.true_negative + self.false_negative
        validate_non_zero_denominator(denominator, "False Omission Rate (FOR)")

        return self.false_negative / denominator

    def get_for(self) -> float:
        """
        Alias for get_false_omission_rate().

        FOR = FN / (TN + FN) = 1 - NPV

        Returns:
            float: False Omission Rate
        """
        return self.get_false_omission_rate()

    def get_false_discovery_rate(self) -> float:
        """
        Calculate False Discovery Rate (FDR).

        FDR = FP / (TP + FP) = 1 - Precision (PPV)

        Represents the probability that a positive prediction is incorrect
        (i.e., the sample is actually negative when predicted positive).

        Returns:
            float: FDR value between 0 and 1

        Raises:
            ValueError: If not binary classification
            ZeroDivisionError: If no predicted positives (TP + FP = 0)
        """
        if self.n_classes != 2:
            raise ValueError("FDR is only available for binary classification")

        from .validation import validate_non_zero_denominator
        denominator = self.true_positive + self.false_positive
        validate_non_zero_denominator(denominator, "False Discovery Rate (FDR)")

        return self.false_positive / denominator

    def get_fdr(self) -> float:
        """
        Alias for get_false_discovery_rate().

        FDR = FP / (TP + FP) = 1 - Precision

        Returns:
            float: False Discovery Rate
        """
        return self.get_false_discovery_rate()

    def get_tpr(self) -> float:
        """
        Alias for get_recall() - True Positive Rate / Sensitivity.

        TPR = TP / (TP + FN)

        Returns:
            float: True Positive Rate
        """
        return self.get_recall()

    def get_tnr(self) -> float:
        """
        Alias for get_specificity() - True Negative Rate.

        TNR = TN / (TN + FP)

        Returns:
            float: True Negative Rate
        """
        return self.get_specificity()

    def get_fpr(self) -> float:
        """
        Alias for get_false_positive_rate().

        FPR = FP / (FP + TN) = 1 - Specificity

        Returns:
            float: False Positive Rate
        """
        return self.get_false_positive_rate()

    def get_fnr(self) -> float:
        """
        Alias for get_false_negative_rate().

        FNR = FN / (FN + TP) = 1 - Recall

        Returns:
            float: False Negative Rate
        """
        return self.get_false_negative_rate()

    def get_ppv(self) -> float:
        """
        Alias for get_precision() - Positive Predictive Value.

        PPV = TP / (TP + FP)

        Returns:
            float: Positive Predictive Value
        """
        return self.get_precision()
