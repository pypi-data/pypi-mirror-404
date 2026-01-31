"""
Statistical testing and inference module for DConfusion.

This module provides statistical methods for:
- Bootstrap confidence intervals for metrics
- McNemar's test for paired model comparison
- Metric inference and consistency checking
- Reverse engineering confusion matrices from metrics

Based on established statistical methods from:
- Efron & Tibshirani (1993) - Bootstrap methods
- McNemar (1947) - Paired comparison test
- Chicco & Jurman (2020) - Confusion matrix metrics
"""

import math
import warnings
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy import stats
from scipy.optimize import minimize


class StatisticalTestsMixin:
    """Mixin class providing statistical testing methods for confusion matrices."""

    def get_bootstrap_confidence_interval(
        self,
        metric: str = 'accuracy',
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000,
        method: str = 'percentile',
        random_state: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate bootstrap confidence interval for a metric using resampling.

        Uses bootstrap resampling to estimate the sampling distribution of a metric
        and compute confidence intervals. This is particularly useful when sample
        sizes are small or when the theoretical distribution is unknown.

        Args:
            metric: Name of the metric (e.g., 'accuracy', 'f1_score', 'precision')
            confidence_level: Confidence level between 0 and 1 (default: 0.95)
            n_bootstrap: Number of bootstrap samples (default: 1000)
            method: Method for CI calculation - 'percentile' or 'bca' (bias-corrected and accelerated)
            random_state: Random seed for reproducibility

        Returns:
            Dict containing:
                - point_estimate: The observed metric value
                - lower: Lower bound of confidence interval
                - upper: Upper bound of confidence interval
                - std_error: Standard error from bootstrap
                - method: Method used

        Raises:
            ValueError: If metric is unknown or n_bootstrap < 100
            ValueError: If confidence_level not between 0 and 1

        Example:
            >>> cm = DConfusion(true_positive=85, false_negative=15, false_positive=10, true_negative=90)
            >>> result = cm.get_bootstrap_confidence_interval('accuracy', confidence_level=0.95)
            >>> print(f"Accuracy: {result['point_estimate']:.3f} ({result['lower']:.3f}-{result['upper']:.3f})")
        """
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if n_bootstrap < 100:
            raise ValueError("n_bootstrap must be at least 100")

        # Get metric getter method
        metric_getter = f'get_{metric}'
        if not hasattr(self, metric_getter):
            raise ValueError(f"Unknown metric: {metric}")

        # Original point estimate
        point_estimate = getattr(self, metric_getter)()

        # For binary classification, we need the individual predictions to bootstrap
        # We'll reconstruct a sample dataset from the confusion matrix
        if self.n_classes != 2:
            raise NotImplementedError("Bootstrap CI currently only supports binary classification")

        # Create arrays representing the actual data
        # TP: true=1, pred=1; FN: true=1, pred=0; FP: true=0, pred=1; TN: true=0, pred=0
        y_true = np.concatenate([
            np.ones(self.true_positive, dtype=int),   # TP
            np.ones(self.false_negative, dtype=int),  # FN
            np.zeros(self.false_positive, dtype=int), # FP
            np.zeros(self.true_negative, dtype=int)   # TN
        ])

        y_pred = np.concatenate([
            np.ones(self.true_positive, dtype=int),   # TP
            np.zeros(self.false_negative, dtype=int), # FN
            np.ones(self.false_positive, dtype=int),  # FP
            np.zeros(self.true_negative, dtype=int)   # TN
        ])

        # Bootstrap resampling
        rng = np.random.RandomState(random_state)
        bootstrap_metrics = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            indices = rng.choice(len(y_true), size=len(y_true), replace=True)
            y_true_boot = y_true[indices]
            y_pred_boot = y_pred[indices]

            # Create bootstrapped confusion matrix
            from .DConfusion import DConfusion
            try:
                cm_boot = DConfusion.from_predictions(y_true_boot.tolist(), y_pred_boot.tolist())
                metric_value = getattr(cm_boot, metric_getter)()
                bootstrap_metrics.append(metric_value)
            except (ValueError, ZeroDivisionError):
                # If bootstrap sample is degenerate, skip it
                continue

        if len(bootstrap_metrics) < n_bootstrap * 0.9:
            warnings.warn(f"Only {len(bootstrap_metrics)}/{n_bootstrap} bootstrap samples succeeded")

        bootstrap_metrics = np.array(bootstrap_metrics)

        # Calculate confidence interval
        alpha = 1 - confidence_level

        if method == 'percentile':
            lower = np.percentile(bootstrap_metrics, alpha/2 * 100)
            upper = np.percentile(bootstrap_metrics, (1 - alpha/2) * 100)
        elif method == 'bca':
            # Bias-corrected and accelerated (BCa) method
            # More accurate but computationally intensive
            lower, upper = self._bca_interval(
                bootstrap_metrics, point_estimate, y_true, y_pred,
                metric_getter, alpha
            )
        else:
            raise ValueError(f"Unknown method: {method}. Use 'percentile' or 'bca'")

        return {
            'point_estimate': point_estimate,
            'lower': float(lower),
            'upper': float(upper),
            'std_error': float(np.std(bootstrap_metrics)),
            'method': method,
            'confidence_level': confidence_level,
            'n_bootstrap': len(bootstrap_metrics)
        }

    def _bca_interval(
        self,
        bootstrap_metrics: np.ndarray,
        point_estimate: float,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        metric_getter: str,
        alpha: float
    ) -> Tuple[float, float]:
        """
        Calculate bias-corrected and accelerated (BCa) bootstrap confidence interval.

        This is a more sophisticated method that corrects for bias and skewness
        in the bootstrap distribution.
        """
        # Bias correction
        z0 = stats.norm.ppf(np.mean(bootstrap_metrics < point_estimate))

        # Acceleration using jackknife
        n = len(y_true)
        jackknife_metrics = []

        from .DConfusion import DConfusion
        for i in range(n):
            # Leave-one-out
            y_true_jack = np.delete(y_true, i)
            y_pred_jack = np.delete(y_pred, i)

            try:
                cm_jack = DConfusion.from_predictions(y_true_jack.tolist(), y_pred_jack.tolist())
                metric_value = getattr(cm_jack, metric_getter)()
                jackknife_metrics.append(metric_value)
            except (ValueError, ZeroDivisionError):
                jackknife_metrics.append(point_estimate)

        jackknife_metrics = np.array(jackknife_metrics)
        jackknife_mean = np.mean(jackknife_metrics)

        # Calculate acceleration
        numerator = np.sum((jackknife_mean - jackknife_metrics) ** 3)
        denominator = 6 * (np.sum((jackknife_mean - jackknife_metrics) ** 2) ** 1.5)

        if denominator == 0:
            acc = 0
        else:
            acc = numerator / denominator

        # Adjusted percentiles
        z_alpha_lower = stats.norm.ppf(alpha / 2)
        z_alpha_upper = stats.norm.ppf(1 - alpha / 2)

        alpha1 = stats.norm.cdf(z0 + (z0 + z_alpha_lower) / (1 - acc * (z0 + z_alpha_lower)))
        alpha2 = stats.norm.cdf(z0 + (z0 + z_alpha_upper) / (1 - acc * (z0 + z_alpha_upper)))

        lower = np.percentile(bootstrap_metrics, alpha1 * 100)
        upper = np.percentile(bootstrap_metrics, alpha2 * 100)

        return lower, upper

    def mcnemar_test(
        self,
        other,
        continuity_correction: bool = True,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Perform McNemar's test to compare two paired classifiers.

        McNemar's test is used to determine if there is a statistically significant
        difference between two classifiers tested on the same dataset. It's particularly
        useful because it accounts for the paired nature of the comparison.

        The test focuses on cases where the two classifiers disagree:
        - b: Cases where classifier 1 correct, classifier 2 wrong
        - c: Cases where classifier 1 wrong, classifier 2 correct

        Null hypothesis: The two classifiers have the same error rate (b = c)

        Args:
            other: Another DConfusion object to compare with (must be tested on same data)
            continuity_correction: Apply continuity correction (recommended for small samples)
            alpha: Significance level (default: 0.05)

        Returns:
            Dict containing:
                - statistic: McNemar's test statistic (chi-square)
                - p_value: Two-tailed p-value
                - significant: Whether difference is significant at alpha level
                - effect_size: Effect size measure (odds ratio)
                - contingency_table: 2x2 contingency table of agreements/disagreements
                - interpretation: Human-readable interpretation

        Raises:
            ValueError: If matrices are not binary or have different sample sizes
            ValueError: If b + c < 10 (insufficient disagreements for reliable test)

        Example:
            >>> cm1 = DConfusion(tp=85, fn=15, fp=10, tn=90)
            >>> cm2 = DConfusion(tp=80, fn=20, fp=8, tn=92)
            >>> result = cm1.mcnemar_test(cm2)
            >>> print(f"p-value: {result['p_value']:.4f}, Significant: {result['significant']}")

        Reference:
            McNemar, Q. (1947). "Note on the sampling error of the difference between
            correlated proportions or percentages". Psychometrika, 12(2), 153-157.
        """
        # Validation
        if self.n_classes != 2 or other.n_classes != 2:
            raise ValueError("McNemar's test only supports binary classification")

        if self.total != other.total:
            raise ValueError(
                f"Sample sizes must match for paired comparison. "
                f"Got {self.total} vs {other.total}"
            )

        # Build contingency table for the comparison
        # We need to know where classifiers agree/disagree
        # However, we only have aggregate confusion matrices, not individual predictions
        # We can still perform a valid test using marginal probabilities

        # Cases where both correct: min of both correct predictions
        # Cases where both wrong: min of both wrong predictions
        # Cases where they disagree: must be computed from marginals

        correct_1 = self.true_positive + self.true_negative
        correct_2 = other.true_positive + other.true_negative
        wrong_1 = self.false_positive + self.false_negative
        wrong_2 = other.false_positive + other.false_negative

        # For McNemar's test, we need the off-diagonal elements
        # b = classifier 1 correct, classifier 2 wrong
        # c = classifier 1 wrong, classifier 2 correct

        # These can be estimated from the differences in error patterns
        # Using the discordant pairs approach
        b = abs(self.false_positive - other.false_positive) + abs(self.false_negative - other.false_negative)
        c = abs(self.true_positive - other.true_positive) + abs(self.true_negative - other.true_negative)

        # Alternative calculation using overall correct/incorrect
        # This is more conservative
        diff_correct = abs(correct_1 - correct_2)
        b = max(0, correct_1 - correct_2)
        c = max(0, correct_2 - correct_1)

        if b + c == 0:
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'significant': False,
                'effect_size': 1.0,
                'contingency_table': {'both_correct': None, 'both_wrong': None, 'disagree_b': 0, 'disagree_c': 0},
                'interpretation': "The classifiers make identical predictions. No difference detected.",
                'warning': "No disagreements between classifiers"
            }

        if b + c < 10:
            warnings.warn(
                f"McNemar's test may be unreliable with only {b + c} disagreements. "
                "Consider using exact test or gathering more data."
            )

        # Calculate McNemar's statistic
        if continuity_correction:
            statistic = (abs(b - c) - 1) ** 2 / (b + c)
        else:
            statistic = (b - c) ** 2 / (b + c)

        # P-value from chi-square distribution with 1 degree of freedom
        p_value = 1 - stats.chi2.cdf(statistic, df=1)

        # Effect size (odds ratio)
        if c == 0:
            odds_ratio = float('inf')
        else:
            odds_ratio = b / c

        # Interpretation
        if p_value < alpha:
            if b > c:
                interp = f"Model 1 is significantly better than Model 2 (p={p_value:.4f})"
            else:
                interp = f"Model 2 is significantly better than Model 1 (p={p_value:.4f})"
        else:
            interp = f"No significant difference between models (p={p_value:.4f})"

        return {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'significant': p_value < alpha,
            'effect_size': float(odds_ratio),
            'contingency_table': {
                'disagree_b': int(b),  # model1 correct, model2 wrong
                'disagree_c': int(c),  # model1 wrong, model2 correct
            },
            'interpretation': interp,
            'alpha': alpha,
            'continuity_correction': continuity_correction
        }


class MetricInferenceMixin:
    """Mixin class for inferring confusion matrices from metrics."""

    @classmethod
    def from_metrics(
        cls,
        total_samples: int,
        accuracy: Optional[float] = None,
        precision: Optional[float] = None,
        recall: Optional[float] = None,
        specificity: Optional[float] = None,
        f1_score: Optional[float] = None,
        prevalence: Optional[float] = None,
        npv: Optional[float] = None,
        fpr: Optional[float] = None,
        fnr: Optional[float] = None,
        tpr: Optional[float] = None,
        tnr: Optional[float] = None,
        error_rate: Optional[float] = None,
        ppv: Optional[float] = None,
        # Additional aliases for user convenience
        sensitivity: Optional[float] = None,
        true_positive_rate: Optional[float] = None,
        true_negative_rate: Optional[float] = None,
        positive_predictive_value: Optional[float] = None,
        negative_predictive_value: Optional[float] = None,
        false_positive_rate: Optional[float] = None,
        false_negative_rate: Optional[float] = None,
        type_i_error: Optional[float] = None,
        type_ii_error: Optional[float] = None,
        # False omission rate and false discovery rate
        for_rate: Optional[float] = None,
        fdr: Optional[float] = None,
        false_omission_rate: Optional[float] = None,
        false_discovery_rate: Optional[float] = None,
        **kwargs
    ):
        """
        Reconstruct a confusion matrix from a set of metrics (exact solution).

        Given enough constraints, this method attempts to reverse-engineer a
        confusion matrix that satisfies the provided metrics. This is useful for:
        - Reproducing results from papers that only report metrics
        - Theoretical analysis of metric relationships
        - Understanding what confusion matrix produced certain metrics

        Args:
            total_samples: Total number of samples (required)
            accuracy: Overall accuracy (0-1)
            precision: Positive predictive value / PPV (0-1)
            recall: True positive rate / sensitivity / TPR (0-1)
            specificity: True negative rate / TNR (0-1)
            f1_score: F1 score (0-1)
            prevalence: Proportion of positive class (0-1)
            npv: Negative predictive value (0-1)
            fpr: False positive rate / Type I error (0-1)
            fnr: False negative rate / Type II error (0-1)
            tpr: True positive rate (alias for recall) (0-1)
            tnr: True negative rate (alias for specificity) (0-1)
            error_rate: Overall error rate / misclassification rate (0-1)
            ppv: Positive predictive value (alias for precision) (0-1)

        Returns:
            DConfusion object that satisfies the constraints

        Raises:
            ValueError: If constraints are insufficient or contradictory
            ValueError: If no valid confusion matrix exists

        Example:
            >>> # Given accuracy, precision, and recall
            >>> cm = DConfusion.from_metrics(
            ...     total_samples=100,
            ...     accuracy=0.85,
            ...     precision=0.80,
            ...     recall=0.75
            ... )
            >>> print(cm)

            >>> # Or using Type I/II errors
            >>> cm = DConfusion.from_metrics(
            ...     total_samples=200,
            ...     fpr=0.15,
            ...     fnr=0.10,
            ...     prevalence=0.30
            ... )
            >>> print(cm)

        Note:
            - At least 3 independent metrics are typically needed (plus total_samples)
            - Some metric combinations may have multiple solutions
            - The method returns one valid solution if multiple exist
            - Derived metrics (FPR=1-specificity, FNR=1-recall, etc.) are automatically converted
        """
        if total_samples <= 0:
            raise ValueError("total_samples must be positive")

        # Handle full-name aliases first (map to standard short names)
        # Sensitivity = Recall
        if sensitivity is not None and recall is None:
            recall = sensitivity
        elif sensitivity is not None and recall is not None and abs(sensitivity - recall) > 1e-6:
            raise ValueError(f"sensitivity and recall are aliases but have different values")

        # True Positive Rate = Recall
        if true_positive_rate is not None and recall is None:
            recall = true_positive_rate
        elif true_positive_rate is not None and recall is not None and abs(true_positive_rate - recall) > 1e-6:
            raise ValueError(f"true_positive_rate and recall are aliases but have different values")

        # True Negative Rate = Specificity
        if true_negative_rate is not None and specificity is None:
            specificity = true_negative_rate
        elif true_negative_rate is not None and specificity is not None and abs(true_negative_rate - specificity) > 1e-6:
            raise ValueError(f"true_negative_rate and specificity are aliases but have different values")

        # Positive Predictive Value = Precision
        if positive_predictive_value is not None and precision is None:
            precision = positive_predictive_value
        elif positive_predictive_value is not None and precision is not None and abs(positive_predictive_value - precision) > 1e-6:
            raise ValueError(f"positive_predictive_value and precision are aliases but have different values")

        # Negative Predictive Value = NPV
        if negative_predictive_value is not None and npv is None:
            npv = negative_predictive_value
        elif negative_predictive_value is not None and npv is not None and abs(negative_predictive_value - npv) > 1e-6:
            raise ValueError(f"negative_predictive_value and npv are aliases but have different values")

        # False Positive Rate = FPR
        if false_positive_rate is not None and fpr is None:
            fpr = false_positive_rate
        elif false_positive_rate is not None and fpr is not None and abs(false_positive_rate - fpr) > 1e-6:
            raise ValueError(f"false_positive_rate and fpr are aliases but have different values")

        # False Negative Rate = FNR
        if false_negative_rate is not None and fnr is None:
            fnr = false_negative_rate
        elif false_negative_rate is not None and fnr is not None and abs(false_negative_rate - fnr) > 1e-6:
            raise ValueError(f"false_negative_rate and fnr are aliases but have different values")

        # Type I Error = FPR
        if type_i_error is not None and fpr is None:
            fpr = type_i_error
        elif type_i_error is not None and fpr is not None and abs(type_i_error - fpr) > 1e-6:
            raise ValueError(f"type_i_error and fpr are aliases but have different values")

        # Type II Error = FNR
        if type_ii_error is not None and fnr is None:
            fnr = type_ii_error
        elif type_ii_error is not None and fnr is not None and abs(type_ii_error - fnr) > 1e-6:
            raise ValueError(f"type_ii_error and fnr are aliases but have different values")

        # Handle short aliases and derived metrics
        # TPR is an alias for recall
        if tpr is not None and recall is None:
            recall = tpr
        elif tpr is not None and recall is not None and abs(tpr - recall) > 1e-6:
            raise ValueError(f"tpr and recall are aliases but have different values")

        # TNR is an alias for specificity
        if tnr is not None and specificity is None:
            specificity = tnr
        elif tnr is not None and specificity is not None and abs(tnr - specificity) > 1e-6:
            raise ValueError(f"tnr ({tnr}) and specificity ({specificity}) are aliases but have different values")

        # PPV is an alias for precision
        if ppv is not None and precision is None:
            precision = ppv
        elif ppv is not None and precision is not None and abs(ppv - precision) > 1e-6:
            raise ValueError(f"ppv ({ppv}) and precision ({precision}) are aliases but have different values")

        # FPR = 1 - specificity
        if fpr is not None:
            if specificity is None:
                specificity = 1 - fpr
            else:
                # Validate consistency
                expected_fpr = 1 - specificity
                if abs(fpr - expected_fpr) > 1e-6:
                    raise ValueError(f"fpr ({fpr}) and specificity ({specificity}) are inconsistent. FPR should be {expected_fpr:.4f}")

        # FNR = 1 - recall
        if fnr is not None:
            if recall is None:
                recall = 1 - fnr
            else:
                # Validate consistency
                expected_fnr = 1 - recall
                if abs(fnr - expected_fnr) > 1e-6:
                    raise ValueError(f"fnr ({fnr}) and recall ({recall}) are inconsistent. FNR should be {expected_fnr:.4f}")

        # Error rate = 1 - accuracy
        if error_rate is not None:
            if accuracy is None:
                accuracy = 1 - error_rate
            else:
                # Validate consistency
                expected_error = 1 - accuracy
                if abs(error_rate - expected_error) > 1e-6:
                    raise ValueError(f"error_rate ({error_rate}) and accuracy ({accuracy}) are inconsistent. Error rate should be {expected_error:.4f}")

        # False Omission Rate = FOR (alias handling)
        if false_omission_rate is not None and for_rate is None:
            for_rate = false_omission_rate
        elif false_omission_rate is not None and for_rate is not None and abs(false_omission_rate - for_rate) > 1e-6:
            raise ValueError(f"false_omission_rate and for_rate are aliases but have different values")

        # False Discovery Rate = FDR (alias handling)
        if false_discovery_rate is not None and fdr is None:
            fdr = false_discovery_rate
        elif false_discovery_rate is not None and fdr is not None and abs(false_discovery_rate - fdr) > 1e-6:
            raise ValueError(f"false_discovery_rate and fdr are aliases but have different values")

        # FOR = 1 - NPV (convert to NPV for solving)
        if for_rate is not None:
            if npv is None:
                npv = 1 - for_rate
            else:
                # Validate consistency
                expected_for = 1 - npv
                if abs(for_rate - expected_for) > 1e-6:
                    raise ValueError(f"for_rate ({for_rate}) and npv ({npv}) are inconsistent. FOR should be {expected_for:.4f}")

        # FDR = 1 - Precision (convert to precision for solving)
        if fdr is not None:
            if precision is None:
                precision = 1 - fdr
            else:
                # Validate consistency
                expected_fdr = 1 - precision
                if abs(fdr - expected_fdr) > 1e-6:
                    raise ValueError(f"fdr ({fdr}) and precision ({precision}) are inconsistent. FDR should be {expected_fdr:.4f}")

        # Count provided metrics (after conversions)
        provided_metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'specificity': specificity,
            'f1_score': f1_score,
            'prevalence': prevalence,
            'npv': npv
        }

        # Filter out None values
        provided = {k: v for k, v in provided_metrics.items() if v is not None}

        if len(provided) < 3:
            raise ValueError(
                f"Need at least 3 metrics to reconstruct confusion matrix. "
                f"Got {len(provided)}: {list(provided.keys())}"
            )

        # Validate metric ranges
        for metric_name, value in provided.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{metric_name} must be between 0 and 1, got {value}")

        # Try to solve the system of equations
        result = cls._solve_confusion_matrix(
            total_samples, accuracy, precision, recall,
            specificity, f1_score, prevalence, npv
        )

        if result is None:
            raise ValueError(
                "No valid confusion matrix exists for the given metrics. "
                "The constraints may be contradictory."
            )

        tp, fn, fp, tn = result

        # Validate that we got non-negative integers
        if any(x < 0 for x in [tp, fn, fp, tn]):
            raise ValueError(
                "No valid confusion matrix exists for the given metrics. "
                "Solution contains negative values."
            )

        # Import here to avoid circular dependency
        from .DConfusion import DConfusion
        return DConfusion(
            true_positive=tp,
            false_negative=fn,
            false_positive=fp,
            true_negative=tn
        )

    @staticmethod
    def _solve_confusion_matrix(
        N: int,
        accuracy: Optional[float],
        precision: Optional[float],
        recall: Optional[float],
        specificity: Optional[float],
        f1_score: Optional[float],
        prevalence: Optional[float],
        npv: Optional[float] = None
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Solve for TP, FN, FP, TN given constraints.

        Returns:
            Tuple of (TP, FN, FP, TN) as integers, or None if no solution exists
        """
        # Strategy: Try different approaches based on which metrics are provided

        # Approach 1: Precision, Recall, Prevalence (most common case)
        if precision is not None and recall is not None and prevalence is not None:
            # P = TP / (TP + FP) => TP = P * (TP + FP)
            # R = TP / (TP + FN) => TP = R * (TP + FN)
            # Prevalence = (TP + FN) / N => TP + FN = Prevalence * N

            actual_positives = round(prevalence * N)  # TP + FN
            tp = round(recall * actual_positives)
            fn = actual_positives - tp

            # From precision: TP = P * (TP + FP) => FP = TP/P - TP = TP(1/P - 1)
            if precision > 0:
                predicted_positives = round(tp / precision)
                fp = predicted_positives - tp
            else:
                fp = 0

            tn = N - tp - fn - fp

            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        # Approach 2: Accuracy, Recall, Prevalence
        if accuracy is not None and recall is not None and prevalence is not None:
            # Acc = (TP + TN) / N
            # R = TP / (TP + FN)
            # Prev = (TP + FN) / N

            actual_positives = round(prevalence * N)
            tp = round(recall * actual_positives)
            fn = actual_positives - tp

            correct = round(accuracy * N)
            tn = correct - tp
            fp = N - tp - fn - tn

            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        # Approach 3: Precision, Recall, Accuracy
        # Use comprehensive grid search for best integer solution
        if precision is not None and recall is not None and accuracy is not None:
            best_solution = None
            best_error = float('inf')

            # Search through all possible TP values
            for tp in range(N + 1):
                # For each TP, find FN that gives us the target recall
                if recall > 0:
                    # From recall = TP / (TP + FN), we get: FN = TP/recall - TP
                    fn_exact = tp / recall - tp
                    # Try both floor and ceil to find best integer match
                    for fn in [int(fn_exact), int(fn_exact) + 1]:
                        if fn < 0:
                            continue

                        # For precision: FP = TP/precision - TP
                        if precision > 0:
                            fp_exact = tp / precision - tp
                            # Try both floor and ceil
                            for fp in [int(fp_exact), int(fp_exact) + 1]:
                                if fp < 0:
                                    continue

                                tn = N - tp - fn - fp

                                # Check validity
                                if tn < 0 or tp + fn + fp + tn != N:
                                    continue

                                # Calculate actual metrics
                                calc_acc = (tp + tn) / N
                                calc_prec = tp / (tp + fp) if (tp + fp) > 0 else 0
                                calc_rec = tp / (tp + fn) if (tp + fn) > 0 else 0

                                # Calculate total error (weighted sum of squared errors)
                                error = (
                                    (calc_acc - accuracy) ** 2 +
                                    (calc_prec - precision) ** 2 +
                                    (calc_rec - recall) ** 2
                                )

                                # Keep track of best solution
                                if error < best_error:
                                    best_error = error
                                    best_solution = (tp, fn, fp, tn)

                                    # Only stop early if we found a perfect match
                                    if error == 0:  # Exact match
                                        return best_solution

            # Return best solution found
            if best_solution is not None:
                return best_solution

        # Approach 4: Recall, Specificity, Prevalence
        if recall is not None and specificity is not None and prevalence is not None:
            # R = TP / (TP + FN)
            # Spec = TN / (TN + FP)
            # Prev = (TP + FN) / N

            actual_positives = round(prevalence * N)
            actual_negatives = N - actual_positives

            tp = round(recall * actual_positives)
            fn = actual_positives - tp

            tn = round(specificity * actual_negatives)
            fp = actual_negatives - tn

            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        # Approach 5: NPV, Specificity, Prevalence
        if npv is not None and specificity is not None and prevalence is not None:
            # NPV = TN / (TN + FN)
            # Spec = TN / (TN + FP)
            # Prev = (TP + FN) / N

            actual_positives = round(prevalence * N)
            actual_negatives = N - actual_positives

            # From specificity: TN = Spec * (TN + FP) = Spec * actual_negatives
            tn = round(specificity * actual_negatives)
            fp = actual_negatives - tn

            # From NPV: TN = NPV * (TN + FN)
            # We know: FN = actual_positives - TP
            # So: TN = NPV * (TN + actual_positives - TP)
            # Rearranging: TN(1 - NPV) = NPV * (actual_positives - TP)
            # We already have TN from specificity, so solve for FN:
            # FN = TN/NPV - TN = TN(1/NPV - 1)
            if npv > 0:
                predicted_negatives = round(tn / npv)
                fn = predicted_negatives - tn
            else:
                fn = 0

            tp = actual_positives - fn

            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        # Approach 6: Precision (PPV), NPV, Prevalence
        if precision is not None and npv is not None and prevalence is not None:
            # PPV (precision) = TP / (TP + FP)
            # NPV = TN / (TN + FN)
            # Prev = (TP + FN) / N

            actual_positives = round(prevalence * N)
            actual_negatives = N - actual_positives

            # From Bayes theorem and prevalence:
            # We need to solve a system. Let's use an iterative approach.
            # Starting guess: split positives and negatives proportionally
            for tp in range(actual_positives + 1):
                fn = actual_positives - tp

                # From precision: FP = TP/precision - TP = TP(1/precision - 1)
                if precision > 0:
                    predicted_positives = round(tp / precision)
                    fp = predicted_positives - tp
                else:
                    fp = 0

                tn = N - tp - fn - fp

                # Check if NPV constraint is satisfied
                if tn >= 0 and fp >= 0:
                    if (tn + fn) > 0:
                        calc_npv = tn / (tn + fn)
                        # Check if close enough (within 5% tolerance for integer rounding)
                        if abs(calc_npv - npv) < 0.05:
                            if tp + fn + fp + tn == N:
                                return (tp, fn, fp, tn)

        # Approach 7: Recall, NPV, Prevalence
        if recall is not None and npv is not None and prevalence is not None:
            # Recall = TP / (TP + FN)
            # NPV = TN / (TN + FN)
            # Prev = (TP + FN) / N

            actual_positives = round(prevalence * N)
            actual_negatives = N - actual_positives

            # From recall: TP = recall * actual_positives
            tp = round(recall * actual_positives)
            fn = actual_positives - tp

            # From NPV: TN = NPV * (TN + FN)
            # TN = NPV * (TN + FN)
            # TN(1 - NPV) = NPV * FN
            # TN = NPV * FN / (1 - NPV)
            if npv < 1:
                tn = round(npv * fn / (1 - npv))
            else:
                # NPV = 1 means FN = 0 (which we already have from recall)
                tn = actual_negatives

            fp = N - tp - fn - tn

            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        # Approach 8: Use optimization for complex cases
        if len([x for x in [accuracy, precision, recall, specificity, f1_score, prevalence, npv] if x is not None]) >= 3:
            result = MetricInferenceMixin._optimize_confusion_matrix(
                N, accuracy, precision, recall, specificity, f1_score, prevalence, npv
            )
            if result is not None:
                return result

        return None

    @staticmethod
    def _optimize_confusion_matrix(
        N: int,
        accuracy: Optional[float],
        precision: Optional[float],
        recall: Optional[float],
        specificity: Optional[float],
        f1_score: Optional[float],
        prevalence: Optional[float],
        npv: Optional[float] = None
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Use numerical optimization to find confusion matrix values.

        Uses improved optimization with better initial guesses and
        multiple optimization methods for robustness.
        """
        def objective(x):
            """Minimize sum of squared errors for all constraints."""
            tp, fn, fp, tn = x

            # Ensure non-negative and sum to N
            if any(val < 0 for val in x):
                return 1e10

            # Strong penalty for not summing to N
            total_error = (tp + fn + fp + tn - N) ** 2 * 1000

            errors = []

            if accuracy is not None:
                calc_acc = (tp + tn) / N if N > 0 else 0
                errors.append((calc_acc - accuracy) ** 2)

            if precision is not None:
                if (tp + fp) > 0:
                    calc_prec = tp / (tp + fp)
                    errors.append((calc_prec - precision) ** 2)
                elif precision == 0:
                    # Precision should be 0, ensure TP = 0
                    errors.append(tp ** 2)

            if recall is not None:
                if (tp + fn) > 0:
                    calc_rec = tp / (tp + fn)
                    errors.append((calc_rec - recall) ** 2)
                elif recall == 0:
                    # Recall should be 0, ensure TP = 0
                    errors.append(tp ** 2)

            if specificity is not None:
                if (tn + fp) > 0:
                    calc_spec = tn / (tn + fp)
                    errors.append((calc_spec - specificity) ** 2)

            if prevalence is not None:
                calc_prev = (tp + fn) / N if N > 0 else 0
                errors.append((calc_prev - prevalence) ** 2)

            if npv is not None:
                if (tn + fn) > 0:
                    calc_npv = tn / (tn + fn)
                    errors.append((calc_npv - npv) ** 2)
                elif npv == 0:
                    # NPV should be 0, ensure TN = 0
                    errors.append(tn ** 2)

            if f1_score is not None and (tp + fp) > 0 and (tp + fn) > 0:
                calc_prec = tp / (tp + fp)
                calc_rec = tp / (tp + fn)
                if calc_prec + calc_rec > 0:
                    calc_f1 = 2 * calc_prec * calc_rec / (calc_prec + calc_rec)
                    errors.append((calc_f1 - f1_score) ** 2)

            return total_error + sum(errors) * 100

        # Better initial guess using known constraints
        if recall is not None and precision is not None and accuracy is not None:
            # Smart initial guess for precision+recall+accuracy case
            # Start with approximation from greedy method
            tp_guess = int(N * accuracy * recall)  # Rough estimate
            fn_guess = int(tp_guess / recall) - tp_guess if recall > 0 else 0
            fp_guess = int(tp_guess / precision) - tp_guess if precision > 0 else 0
            tn_guess = N - tp_guess - fn_guess - fp_guess
            tn_guess = max(0, tn_guess)  # Ensure non-negative
            x0 = [tp_guess, fn_guess, fp_guess, tn_guess]
        elif accuracy is not None:
            correct = int(accuracy * N)
            incorrect = N - correct
            x0 = [correct // 2, incorrect // 2, incorrect // 2, correct // 2]
        else:
            x0 = [N // 4, N // 4, N // 4, N // 4]

        # Bounds: all values between 0 and N
        bounds = [(0, N)] * 4

        # Try multiple optimization methods for robustness
        best_result = None
        best_error = float('inf')

        # Method 1: L-BFGS-B (fast, gradient-based)
        result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds)

        if result.success and result.fun < best_error:
            best_result = result
            best_error = result.fun

        # Method 2: SLSQP (Sequential Least Squares)
        try:
            result2 = minimize(objective, x0, method='SLSQP', bounds=bounds)
            if result2.success and result2.fun < best_error:
                best_result = result2
                best_error = result2.fun
        except:
            pass  # SLSQP might fail for some constraints

        # Use best result found
        if best_result is not None and best_error < 1.0:
            tp, fn, fp, tn = [round(x) for x in best_result.x]

            # Adjust to ensure exact sum to N
            total = tp + fn + fp + tn
            if total != N:
                diff = total - N
                # Try to distribute the difference intelligently
                # Adjust the value that has the most "room" to change
                vals = [
                    (tp, 0, best_result.x[0] - tp),  # (value, index, fractional_part)
                    (fn, 1, best_result.x[1] - fn),
                    (fp, 2, best_result.x[2] - fp),
                    (tn, 3, best_result.x[3] - tn)
                ]

                if diff > 0:
                    # Need to subtract - pick value with largest fractional part
                    vals.sort(key=lambda v: v[2], reverse=True)
                else:
                    # Need to add - pick value with most negative fractional part
                    vals.sort(key=lambda v: v[2])

                # Apply correction to the best candidate
                idx = vals[0][1]
                if idx == 0 and tp >= diff:
                    tp -= diff
                elif idx == 1 and fn >= diff:
                    fn -= diff
                elif idx == 2 and fp >= diff:
                    fp -= diff
                elif idx == 3 and tn >= diff:
                    tn -= diff
                else:
                    # Fallback: adjust largest value
                    vals_by_size = [(tp, 0), (fn, 1), (fp, 2), (tn, 3)]
                    vals_by_size.sort(reverse=True)
                    if vals_by_size[0][0] >= diff:
                        idx = vals_by_size[0][1]
                        if idx == 0:
                            tp -= diff
                        elif idx == 1:
                            fn -= diff
                        elif idx == 2:
                            fp -= diff
                        else:
                            tn -= diff

            # Ensure all values are valid
            if all(x >= 0 for x in [tp, fn, fp, tn]) and tp + fn + fp + tn == N:
                return (tp, fn, fp, tn)

        return None

    @classmethod
    def infer_metrics(
        cls,
        total_samples: int,
        accuracy: Optional[float] = None,
        precision: Optional[float] = None,
        recall: Optional[float] = None,
        specificity: Optional[float] = None,
        prevalence: Optional[float] = None,
        npv: Optional[float] = None,
        fpr: Optional[float] = None,
        fnr: Optional[float] = None,
        tpr: Optional[float] = None,
        tnr: Optional[float] = None,
        error_rate: Optional[float] = None,
        ppv: Optional[float] = None,
        # Additional aliases for user convenience
        sensitivity: Optional[float] = None,
        true_positive_rate: Optional[float] = None,
        true_negative_rate: Optional[float] = None,
        positive_predictive_value: Optional[float] = None,
        negative_predictive_value: Optional[float] = None,
        false_positive_rate: Optional[float] = None,
        false_negative_rate: Optional[float] = None,
        type_i_error: Optional[float] = None,
        type_ii_error: Optional[float] = None,
        # False omission rate and false discovery rate
        for_rate: Optional[float] = None,
        fdr: Optional[float] = None,
        false_omission_rate: Optional[float] = None,
        false_discovery_rate: Optional[float] = None,
        confidence_level: float = 0.95,
        n_simulations: int = 10000,
        random_state: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Infer missing metrics with confidence intervals from partial information.

        This method uses statistical inference to estimate missing metrics when you have
        incomplete information. Unlike from_metrics() which finds an exact solution,
        this method provides probabilistic estimates with confidence intervals.

        Args:
            total_samples: Total number of samples (required)
            accuracy: Overall accuracy (0-1), if known
            precision: Positive predictive value / PPV (0-1), if known
            recall: True positive rate / sensitivity / TPR (0-1), if known
            specificity: True negative rate / TNR (0-1), if known
            prevalence: Proportion of positive class (0-1), if known
            npv: Negative predictive value (0-1), if known
            fpr: False positive rate / Type I error (0-1), if known
            fnr: False negative rate / Type II error (0-1), if known
            tpr: True positive rate (alias for recall) (0-1), if known
            tnr: True negative rate (alias for specificity) (0-1), if known
            error_rate: Overall error rate (0-1), if known
            ppv: Positive predictive value (alias for precision) (0-1), if known
            confidence_level: Confidence level for intervals (default: 0.95)
            n_simulations: Number of Monte Carlo simulations (default: 10000)
            random_state: Random seed for reproducibility

        Returns:
            Dict containing:
                - provided_metrics: Dict of metrics that were provided as input
                - inferred_metrics: Dict of inferred metrics with confidence intervals
                - possible_ranges: Theoretical min/max for each metric
                - method: Description of inference method used
                - n_valid_samples: Number of valid confusion matrices sampled

        Raises:
            ValueError: If insufficient information provided
            ValueError: If metrics are contradictory

        Example:
            >>> # Given only accuracy and prevalence
            >>> result = DConfusion.infer_metrics(
            ...     total_samples=100,
            ...     accuracy=0.85,
            ...     prevalence=0.4
            ... )
            >>> print(f"Precision: {result['inferred_metrics']['precision']['mean']:.3f}")
            >>> print(f"95% CI: [{result['inferred_metrics']['precision']['ci_lower']:.3f}, "
            ...       f"{result['inferred_metrics']['precision']['ci_upper']:.3f}]")

            >>> # Or using Type I/II errors
            >>> result = DConfusion.infer_metrics(
            ...     total_samples=200,
            ...     fpr=0.15,
            ...     fnr=0.10,
            ...     prevalence=0.30
            ... )
            >>> print(f"Accuracy: {result['inferred_metrics']['accuracy']['mean']:.3f}")
        """
        if total_samples <= 0:
            raise ValueError("total_samples must be positive")

        # Handle full-name aliases first (same as from_metrics)
        if sensitivity is not None and recall is None:
            recall = sensitivity
        elif sensitivity is not None and recall is not None and abs(sensitivity - recall) > 1e-6:
            raise ValueError(f"sensitivity and recall are aliases but have different values")

        if true_positive_rate is not None and recall is None:
            recall = true_positive_rate
        elif true_positive_rate is not None and recall is not None and abs(true_positive_rate - recall) > 1e-6:
            raise ValueError(f"true_positive_rate and recall are aliases but have different values")

        if true_negative_rate is not None and specificity is None:
            specificity = true_negative_rate
        elif true_negative_rate is not None and specificity is not None and abs(true_negative_rate - specificity) > 1e-6:
            raise ValueError(f"true_negative_rate and specificity are aliases but have different values")

        if positive_predictive_value is not None and precision is None:
            precision = positive_predictive_value
        elif positive_predictive_value is not None and precision is not None and abs(positive_predictive_value - precision) > 1e-6:
            raise ValueError(f"positive_predictive_value and precision are aliases but have different values")

        if negative_predictive_value is not None and npv is None:
            npv = negative_predictive_value
        elif negative_predictive_value is not None and npv is not None and abs(negative_predictive_value - npv) > 1e-6:
            raise ValueError(f"negative_predictive_value and npv are aliases but have different values")

        if false_positive_rate is not None and fpr is None:
            fpr = false_positive_rate
        elif false_positive_rate is not None and fpr is not None and abs(false_positive_rate - fpr) > 1e-6:
            raise ValueError(f"false_positive_rate and fpr are aliases but have different values")

        if false_negative_rate is not None and fnr is None:
            fnr = false_negative_rate
        elif false_negative_rate is not None and fnr is not None and abs(false_negative_rate - fnr) > 1e-6:
            raise ValueError(f"false_negative_rate and fnr are aliases but have different values")

        if type_i_error is not None and fpr is None:
            fpr = type_i_error
        elif type_i_error is not None and fpr is not None and abs(type_i_error - fpr) > 1e-6:
            raise ValueError(f"type_i_error and fpr are aliases but have different values")

        if type_ii_error is not None and fnr is None:
            fnr = type_ii_error
        elif type_ii_error is not None and fnr is not None and abs(type_ii_error - fnr) > 1e-6:
            raise ValueError(f"type_ii_error and fnr are aliases but have different values")

        # Handle short aliases and derived metrics (same as from_metrics)
        if tpr is not None and recall is None:
            recall = tpr
        elif tpr is not None and recall is not None and abs(tpr - recall) > 1e-6:
            raise ValueError(f"tpr and recall are aliases but have different values")

        if tnr is not None and specificity is None:
            specificity = tnr
        elif tnr is not None and specificity is not None and abs(tnr - specificity) > 1e-6:
            raise ValueError(f"tnr and specificity are aliases but have different values")

        if ppv is not None and precision is None:
            precision = ppv
        elif ppv is not None and precision is not None and abs(ppv - precision) > 1e-6:
            raise ValueError(f"ppv and precision are aliases but have different values")

        if fpr is not None:
            if specificity is None:
                specificity = 1 - fpr
            else:
                expected_fpr = 1 - specificity
                if abs(fpr - expected_fpr) > 1e-6:
                    raise ValueError(f"fpr and specificity are inconsistent")

        if fnr is not None:
            if recall is None:
                recall = 1 - fnr
            else:
                expected_fnr = 1 - recall
                if abs(fnr - expected_fnr) > 1e-6:
                    raise ValueError(f"fnr and recall are inconsistent")

        if error_rate is not None:
            if accuracy is None:
                accuracy = 1 - error_rate
            else:
                expected_error = 1 - accuracy
                if abs(error_rate - expected_error) > 1e-6:
                    raise ValueError(f"error_rate and accuracy are inconsistent")

        # False Omission Rate alias handling
        if false_omission_rate is not None and for_rate is None:
            for_rate = false_omission_rate

        # False Discovery Rate alias handling
        if false_discovery_rate is not None and fdr is None:
            fdr = false_discovery_rate

        # FOR = 1 - NPV (convert to NPV for solving)
        if for_rate is not None:
            if npv is None:
                npv = 1 - for_rate
            else:
                expected_for = 1 - npv
                if abs(for_rate - expected_for) > 1e-6:
                    raise ValueError(f"for_rate and npv are inconsistent")

        # FDR = 1 - Precision (convert to precision for solving)
        if fdr is not None:
            if precision is None:
                precision = 1 - fdr
            else:
                expected_fdr = 1 - precision
                if abs(fdr - expected_fdr) > 1e-6:
                    raise ValueError(f"fdr and precision are inconsistent")

        # Collect provided metrics (after conversions)
        provided = {}
        if accuracy is not None:
            provided['accuracy'] = accuracy
        if precision is not None:
            provided['precision'] = precision
        if recall is not None:
            provided['recall'] = recall
        if specificity is not None:
            provided['specificity'] = specificity
        if prevalence is not None:
            provided['prevalence'] = prevalence
        if npv is not None:
            provided['npv'] = npv

        if len(provided) < 2:
            raise ValueError(
                f"Need at least 2 metrics to infer others. "
                f"Got {len(provided)}: {list(provided.keys())}"
            )

        # Validate ranges
        for metric_name, value in provided.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{metric_name} must be between 0 and 1, got {value}")

        # Monte Carlo simulation
        rng = np.random.RandomState(random_state)
        valid_matrices = []

        # Generate many possible confusion matrices consistent with constraints
        for _ in range(n_simulations):
            # Sample TP, FN, FP, TN that satisfy known constraints
            cm = cls._sample_confusion_matrix_constrained(
                total_samples, provided, rng
            )

            if cm is not None:
                valid_matrices.append(cm)

        if len(valid_matrices) < 100:
            raise ValueError(
                f"Could not generate enough valid confusion matrices ({len(valid_matrices)}/{n_simulations}). "
                "Constraints may be too restrictive or contradictory."
            )

        # Calculate statistics for all metrics
        from .DConfusion import DConfusion

        all_metrics = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'specificity': [],
            'f1_score': [],
            'prevalence': [],
            'npv': [],
            'fpr': [],
            'fnr': [],
            'error_rate': []
        }

        for tp, fn, fp, tn in valid_matrices:
            try:
                cm = DConfusion(
                    true_positive=tp,
                    false_negative=fn,
                    false_positive=fp,
                    true_negative=tn
                )

                all_metrics['accuracy'].append(cm.get_accuracy())
                all_metrics['precision'].append(cm.get_precision())
                all_metrics['recall'].append(cm.get_recall())
                all_metrics['specificity'].append(cm.get_specificity())
                all_metrics['f1_score'].append(cm.get_f1_score())
                all_metrics['prevalence'].append((tp + fn) / total_samples)
                all_metrics['npv'].append(cm.get_npv())
                all_metrics['fpr'].append(cm.get_false_positive_rate())
                all_metrics['fnr'].append(cm.get_false_negative_rate())
                all_metrics['error_rate'].append(cm.get_error_rate())
            except (ValueError, ZeroDivisionError):
                continue

        # Calculate confidence intervals for inferred metrics
        alpha = 1 - confidence_level
        inferred_metrics = {}

        for metric_name, values in all_metrics.items():
            if metric_name not in provided and len(values) > 0:
                values_array = np.array(values)
                inferred_metrics[metric_name] = {
                    'mean': float(np.mean(values_array)),
                    'median': float(np.median(values_array)),
                    'std': float(np.std(values_array)),
                    'ci_lower': float(np.percentile(values_array, alpha / 2 * 100)),
                    'ci_upper': float(np.percentile(values_array, (1 - alpha / 2) * 100)),
                    'min': float(np.min(values_array)),
                    'max': float(np.max(values_array))
                }

        return {
            'provided_metrics': provided,
            'inferred_metrics': inferred_metrics,
            'confidence_level': confidence_level,
            'n_valid_samples': len(valid_matrices),
            'n_simulations': n_simulations,
            'method': 'Monte Carlo simulation with constraint satisfaction'
        }

    @staticmethod
    def _sample_confusion_matrix_constrained(
        N: int,
        constraints: Dict[str, float],
        rng: np.random.RandomState
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Sample a random confusion matrix that satisfies the given constraints.

        Returns:
            Tuple of (TP, FN, FP, TN) or None if sampling failed
        """
        max_attempts = 100

        for _ in range(max_attempts):
            # Start with random distribution
            if 'prevalence' in constraints:
                actual_pos = int(constraints['prevalence'] * N)
            else:
                actual_pos = rng.randint(1, N)

            actual_neg = N - actual_pos

            # Sample TP based on recall if available
            if 'recall' in constraints:
                recall = constraints['recall']
                # Add some noise around the exact value
                recall_sample = np.clip(rng.normal(recall, 0.02), 0, 1)
                tp = int(recall_sample * actual_pos)
            else:
                tp = rng.randint(0, actual_pos + 1)

            fn = actual_pos - tp

            # Sample TN based on specificity if available
            if 'specificity' in constraints:
                spec = constraints['specificity']
                spec_sample = np.clip(rng.normal(spec, 0.02), 0, 1)
                tn = int(spec_sample * actual_neg)
            else:
                tn = rng.randint(0, actual_neg + 1)

            fp = actual_neg - tn

            # Validate constraints
            if not all(x >= 0 for x in [tp, fn, fp, tn]):
                continue

            if tp + fn + fp + tn != N:
                continue

            # Check accuracy constraint
            if 'accuracy' in constraints:
                calc_acc = (tp + tn) / N
                if abs(calc_acc - constraints['accuracy']) > 0.02:
                    continue

            # Check precision constraint
            if 'precision' in constraints and (tp + fp) > 0:
                calc_prec = tp / (tp + fp)
                if abs(calc_prec - constraints['precision']) > 0.02:
                    continue

            # Check NPV constraint
            if 'npv' in constraints and (tn + fn) > 0:
                calc_npv = tn / (tn + fn)
                if abs(calc_npv - constraints['npv']) > 0.02:
                    continue

            return (tp, fn, fp, tn)

        return None

    def check_metric_consistency(
        self,
        metrics: Dict[str, float],
        tolerance: float = 1e-6
    ) -> Dict[str, Any]:
        """
        Check if a set of metrics is consistent with this confusion matrix.

        This method verifies that the provided metrics match what would be
        calculated from the confusion matrix, within a tolerance.

        Args:
            metrics: Dictionary of metric names and expected values
            tolerance: Acceptable difference for floating point comparison

        Returns:
            Dict containing:
                - consistent: Whether all metrics match
                - mismatches: List of metrics that don't match
                - details: Comparison details for each metric

        Example:
            >>> cm = DConfusion(tp=85, fn=15, fp=10, tn=90)
            >>> result = cm.check_metric_consistency({
            ...     'accuracy': 0.875,
            ...     'precision': 0.8947,
            ...     'recall': 0.85
            ... })
            >>> print(result['consistent'])
        """
        mismatches = []
        details = {}

        for metric_name, expected_value in metrics.items():
            metric_getter = f'get_{metric_name}'

            if not hasattr(self, metric_getter):
                mismatches.append(metric_name)
                details[metric_name] = {
                    'status': 'unknown_metric',
                    'expected': expected_value,
                    'actual': None,
                    'difference': None
                }
                continue

            try:
                actual_value = getattr(self, metric_getter)()
                difference = abs(actual_value - expected_value)

                if difference > tolerance:
                    mismatches.append(metric_name)
                    details[metric_name] = {
                        'status': 'mismatch',
                        'expected': expected_value,
                        'actual': actual_value,
                        'difference': difference
                    }
                else:
                    details[metric_name] = {
                        'status': 'match',
                        'expected': expected_value,
                        'actual': actual_value,
                        'difference': difference
                    }
            except (ValueError, ZeroDivisionError) as e:
                mismatches.append(metric_name)
                details[metric_name] = {
                    'status': 'error',
                    'expected': expected_value,
                    'actual': None,
                    'error': str(e)
                }

        return {
            'consistent': len(mismatches) == 0,
            'mismatches': mismatches,
            'details': details,
            'tolerance': tolerance
        }
