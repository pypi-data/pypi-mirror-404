"""
Consistency testing for confusion matrices.

This module wraps mlscorecheck by Fazekas & Kovács (2024) to provide
consistency testing capabilities - verifying whether reported performance
scores could mathematically result from a given experimental setup.

Paper: https://doi.org/10.1016/j.asoc.2024.111993
Package: https://github.com/FalseNegativeLab/mlscorecheck

If you use these features in your research, please cite:

    Fazekas, A., & Kovács, G. (2024). Testing the consistency of
    performance scores reported for binary classification problems.
    Applied Soft Computing, 164, 111993.

Key Concepts:
    - Consistency Testing: Given reported scores and experimental setup (p, n),
      determine if ANY valid confusion matrix could produce those scores.
    - This is different from reconstruction (from_metrics) which finds a specific matrix.
    - Consistency testing returns a boolean with mathematical certainty (no false positives).

Example:
    >>> from dconfusion import check_consistency
    >>>
    >>> # Check if reported scores are mathematically possible
    >>> result = check_consistency(
    ...     p=50, n=100,
    ...     scores={"acc": 0.85, "sens": 0.90, "spec": 0.82}
    ... )
    >>> print(f"Scores are consistent: {result.is_consistent}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Iterator, Union
import warnings


# Check if mlscorecheck is available
try:
    import mlscorecheck
    from mlscorecheck.check.binary import check_1_testset_no_kfold
    HAS_MLSCORECHECK = True
    MLSCORECHECK_VERSION = getattr(mlscorecheck, '__version__', 'unknown')
except ImportError:
    HAS_MLSCORECHECK = False
    MLSCORECHECK_VERSION = None


def _require_mlscorecheck():
    """Raise ImportError if mlscorecheck is not installed."""
    if not HAS_MLSCORECHECK:
        raise ImportError(
            "Consistency testing requires 'mlscorecheck' by Fazekas & Kovács (2024).\n"
            "Install with: pip install mlscorecheck\n"
            "Or install dconfusion with consistency extras: pip install dconfusion[consistency]\n\n"
            "Reference: https://github.com/FalseNegativeLab/mlscorecheck"
        )


@dataclass
class ConsistencyResult:
    """
    Result of a consistency test.

    Attributes:
        is_consistent: True if the scores could result from the experimental setup.
                      False means the scores are DEFINITELY inconsistent (mathematical certainty).
        scores_tested: The scores that were tested.
        p: Number of positive samples in the experimental setup.
        n: Number of negative samples in the experimental setup.
        epsilon: Numerical uncertainty used for rounding tolerance.
        details: Raw result from mlscorecheck (if available).
        message: Human-readable interpretation of the result.
    """
    is_consistent: bool
    scores_tested: Dict[str, float]
    p: int
    n: int
    epsilon: float
    details: Optional[Dict[str, Any]] = None
    message: str = ""

    def __bool__(self) -> bool:
        """Allow using result directly in boolean context."""
        return self.is_consistent

    def __repr__(self) -> str:
        status = "CONSISTENT" if self.is_consistent else "INCONSISTENT"
        return f"ConsistencyResult({status}, p={self.p}, n={self.n}, scores={self.scores_tested})"


@dataclass
class AggregatedConsistencyResult:
    """
    Result of consistency test for aggregated (k-fold) scores.

    Attributes:
        is_consistent: True if scores could result from the k-fold setup.
        aggregation: The aggregation method tested ("mos" or "som").
        folds: The fold configuration tested.
        scores_tested: The scores that were tested.
        epsilon: Numerical uncertainty used.
        details: Raw result from mlscorecheck.
        message: Human-readable interpretation.
    """
    is_consistent: bool
    aggregation: str
    folds: List[Dict[str, int]]
    scores_tested: Dict[str, float]
    epsilon: float
    details: Optional[Dict[str, Any]] = None
    message: str = ""

    def __bool__(self) -> bool:
        return self.is_consistent


# Score name mapping from DConfusion conventions to mlscorecheck conventions
SCORE_NAME_MAP = {
    # Standard names
    "accuracy": "acc",
    "sensitivity": "sens",
    "recall": "sens",
    "specificity": "spec",
    "precision": "ppv",
    "ppv": "ppv",
    "npv": "npv",
    "f1_score": "f1p",
    "f1": "f1p",
    "f_measure": "f1p",
    "mcc": "mcc",
    "matthews_correlation_coefficient": "mcc",
    "balanced_accuracy": "bacc",
    "bacc": "bacc",
    # Rate aliases
    "tpr": "sens",
    "tnr": "spec",
    "fpr": "fpr",
    "fnr": "fnr",
    "false_positive_rate": "fpr",
    "false_negative_rate": "fnr",
    # Short forms (pass through)
    "acc": "acc",
    "sens": "sens",
    "spec": "spec",
}


def _map_score_names(scores: Dict[str, float]) -> Dict[str, float]:
    """Map DConfusion score names to mlscorecheck names."""
    mapped = {}
    for name, value in scores.items():
        mapped_name = SCORE_NAME_MAP.get(name.lower(), name.lower())
        mapped[mapped_name] = value
    return mapped


def _infer_epsilon(scores: Dict[str, float]) -> float:
    """
    Infer epsilon (numerical uncertainty) from decimal places in scores.

    If a score is reported as 0.857, we assume uncertainty of ±0.0005
    (half of the last decimal place).
    """
    max_decimals = 0
    for value in scores.values():
        str_val = f"{value:.10f}".rstrip('0')
        if '.' in str_val:
            decimals = len(str_val.split('.')[1])
            max_decimals = max(max_decimals, decimals)

    if max_decimals == 0:
        return 0.5  # Integer values
    return 10 ** (-max_decimals) / 2


def check_consistency(
    p: int,
    n: int,
    scores: Dict[str, float],
    epsilon: Optional[float] = None,
) -> ConsistencyResult:
    """
    Test if reported scores are consistent with an experimental setup.

    This function uses mlscorecheck (Fazekas & Kovács, 2024) to determine
    whether the reported performance scores could mathematically result
    from a confusion matrix with the given number of positive (p) and
    negative (n) samples.

    IMPORTANT: If this returns is_consistent=False, the scores are
    DEFINITELY impossible - there is no valid confusion matrix that
    could produce them. This is a mathematical certainty, not a
    statistical inference.

    Args:
        p: Number of positive samples in the evaluation set.
        n: Number of negative samples in the evaluation set.
        scores: Dictionary mapping score names to values.
                Supported scores: acc, sens, spec, ppv, npv, f1, mcc, bacc, etc.
        epsilon: Numerical uncertainty for rounding tolerance.
                If None, inferred from decimal places in scores.

    Returns:
        ConsistencyResult with is_consistent boolean and details.

    Raises:
        ImportError: If mlscorecheck is not installed.
        ValueError: If p or n are not positive integers.

    Example:
        >>> # These scores are mathematically possible
        >>> result = check_consistency(
        ...     p=50, n=100,
        ...     scores={"acc": 0.85, "sens": 0.90, "spec": 0.82}
        ... )
        >>> print(result.is_consistent)  # True

        >>> # These scores are mathematically IMPOSSIBLE
        >>> result = check_consistency(
        ...     p=50, n=100,
        ...     scores={"acc": 0.99, "sens": 0.50, "spec": 0.50}
        ... )
        >>> print(result.is_consistent)  # False - accuracy can't be 0.99
        ...                               # if both sens and spec are only 0.50

    Reference:
        Fazekas, A., & Kovács, G. (2024). Testing the consistency of
        performance scores reported for binary classification problems.
        Applied Soft Computing, 164, 111993.
    """
    _require_mlscorecheck()

    if p <= 0 or n <= 0:
        raise ValueError(f"p and n must be positive integers. Got p={p}, n={n}")

    if not scores:
        raise ValueError("At least one score must be provided")

    # Map score names and infer epsilon
    mapped_scores = _map_score_names(scores)
    eps = epsilon if epsilon is not None else _infer_epsilon(scores)

    try:
        # Call mlscorecheck's consistency test
        result = check_1_testset_no_kfold(
            testset={'p': p, 'n': n},
            scores=mapped_scores,
            eps=eps
        )

        is_consistent = not result.get('inconsistency', False)

        if is_consistent:
            message = (
                f"Scores are CONSISTENT with experimental setup (p={p}, n={n}). "
                f"At least one valid confusion matrix exists that produces these scores."
            )
        else:
            message = (
                f"Scores are INCONSISTENT with experimental setup (p={p}, n={n}). "
                f"No valid confusion matrix can produce these scores. "
                f"This indicates either: (1) incorrect experimental setup assumed, "
                f"(2) typographical errors in reported scores, or "
                f"(3) methodological issues in how scores were calculated."
            )

        return ConsistencyResult(
            is_consistent=is_consistent,
            scores_tested=scores,
            p=p,
            n=n,
            epsilon=eps,
            details=result,
            message=message
        )

    except Exception as e:
        # If mlscorecheck raises an error, wrap it with context
        raise RuntimeError(
            f"Error during consistency check: {str(e)}. "
            f"Scores: {scores}, p={p}, n={n}, epsilon={eps}"
        ) from e


def check_consistency_kfold(
    folds: List[Tuple[int, int]],
    scores: Dict[str, float],
    aggregation: str = "mos",
    epsilon: Optional[float] = None,
) -> AggregatedConsistencyResult:
    """
    Test consistency for k-fold cross-validation aggregated scores.

    When performance scores are reported from k-fold cross-validation,
    they are typically aggregated in one of two ways:

    - MoS (Mean of Scores): Calculate score for each fold, then average.
      This is the most common approach.

    - SoM (Score of Means): Sum TP, TN, FP, FN across folds, then calculate scores.
      Equivalent to a single confusion matrix with totals.

    Args:
        folds: List of (p_i, n_i) tuples, one per fold.
               p_i = positives in fold i, n_i = negatives in fold i.
        scores: Dictionary of aggregated score names to values.
        aggregation: "mos" (Mean of Scores) or "som" (Score of Means).
        epsilon: Numerical uncertainty. If None, inferred from scores.

    Returns:
        AggregatedConsistencyResult with is_consistent boolean.

    Example:
        >>> # 5-fold CV with stratified splits
        >>> folds = [(10, 90), (10, 90), (10, 90), (10, 90), (10, 90)]
        >>> result = check_consistency_kfold(
        ...     folds=folds,
        ...     scores={"acc": 0.85, "sens": 0.75, "spec": 0.86},
        ...     aggregation="mos"
        ... )
        >>> print(result.is_consistent)

    Note:
        For MoS aggregation with non-linear scores (like F1, MCC), only
        acc, sens, spec, and bacc are supported due to the ILP formulation.
    """
    _require_mlscorecheck()

    if not folds:
        raise ValueError("At least one fold must be provided")

    if aggregation.lower() not in ("mos", "som"):
        raise ValueError(f"aggregation must be 'mos' or 'som', got '{aggregation}'")

    # Convert folds to mlscorecheck format
    fold_dicts = [{'p': p, 'n': n} for p, n in folds]

    mapped_scores = _map_score_names(scores)
    eps = epsilon if epsilon is not None else _infer_epsilon(scores)

    try:
        if aggregation.lower() == "som":
            # SoM: equivalent to single matrix with totals
            from mlscorecheck.check.binary import check_1_dataset_known_folds_som
            result = check_1_dataset_known_folds_som(
                dataset={'folds': fold_dicts},
                scores=mapped_scores,
                eps=eps
            )
        else:
            # MoS: requires ILP, only supports linear scores
            from mlscorecheck.check.binary import check_1_dataset_known_folds_mos

            # Check for unsupported scores
            linear_scores = {'acc', 'sens', 'spec', 'bacc', 'accuracy', 'sensitivity',
                           'specificity', 'balanced_accuracy'}
            unsupported = set(mapped_scores.keys()) - linear_scores
            if unsupported:
                warnings.warn(
                    f"MoS aggregation only supports linear scores (acc, sens, spec, bacc). "
                    f"Unsupported scores will be ignored: {unsupported}"
                )
                mapped_scores = {k: v for k, v in mapped_scores.items() if k in linear_scores}

            result = check_1_dataset_known_folds_mos(
                dataset={'folds': fold_dicts},
                scores=mapped_scores,
                eps=eps
            )

        is_consistent = not result.get('inconsistency', False)

        if is_consistent:
            message = f"Scores are CONSISTENT with {len(folds)}-fold CV ({aggregation.upper()} aggregation)."
        else:
            message = (
                f"Scores are INCONSISTENT with {len(folds)}-fold CV ({aggregation.upper()} aggregation). "
                f"No valid fold-level confusion matrices can produce these aggregated scores."
            )

        return AggregatedConsistencyResult(
            is_consistent=is_consistent,
            aggregation=aggregation.lower(),
            folds=fold_dicts,
            scores_tested=scores,
            epsilon=eps,
            details=result,
            message=message
        )

    except Exception as e:
        raise RuntimeError(
            f"Error during k-fold consistency check: {str(e)}. "
            f"Folds: {folds}, scores: {scores}, aggregation: {aggregation}"
        ) from e


def enumerate_fold_configurations(
    p: int,
    n: int,
    k: int
) -> Iterator[Tuple[List[int], List[int]]]:
    """
    Generate all valid k-fold configurations for given p positives and n negatives.

    This is useful when you don't know the exact fold configuration used
    in a k-fold CV experiment. You can test consistency against all possible
    configurations.

    A configuration is valid if:
    - Each fold has approximately (p+n)/k samples
    - At least 2 folds have positives (for valid training sets)
    - At least 2 folds have negatives (for valid training sets)

    Args:
        p: Total number of positive samples.
        n: Total number of negative samples.
        k: Number of folds.

    Yields:
        Tuple of (p_list, n_list) where p_list[i] and n_list[i] are the
        number of positives and negatives in fold i.

    Example:
        >>> # Small dataset, 3 folds
        >>> for p_vec, n_vec in enumerate_fold_configurations(p=6, n=12, k=3):
        ...     print(f"Folds: {list(zip(p_vec, n_vec))}")

    Warning:
        The number of configurations can be very large for balanced datasets.
        For imbalanced datasets, it's typically manageable.
    """
    _require_mlscorecheck()

    if p <= 0 or n <= 0:
        raise ValueError(f"p and n must be positive. Got p={p}, n={n}")
    if k < 2:
        raise ValueError(f"k must be at least 2. Got k={k}")
    if k > p + n:
        raise ValueError(f"k cannot exceed total samples. Got k={k}, p+n={p+n}")

    try:
        from mlscorecheck.check.binary import create_folding_generator

        generator = create_folding_generator(
            dataset={'p': p, 'n': n},
            folding={'n_folds': k}
        )

        for fold_config in generator:
            # Extract p and n lists from fold config
            p_list = [f['p'] for f in fold_config['folds']]
            n_list = [f['n'] for f in fold_config['folds']]
            yield (p_list, n_list)

    except ImportError:
        # Fallback: implement basic enumeration if mlscorecheck doesn't have this
        raise NotImplementedError(
            "Fold enumeration requires mlscorecheck with fold generation support"
        )


def get_stratified_fold_configuration(
    p: int,
    n: int,
    k: int
) -> List[Tuple[int, int]]:
    """
    Get the fold configuration for stratified k-fold CV (sklearn-style).

    When stratification is used, each fold has approximately the same
    class distribution as the full dataset. This function returns the
    exact configuration that sklearn's StratifiedKFold would produce.

    Args:
        p: Total number of positive samples.
        n: Total number of negative samples.
        k: Number of folds.

    Returns:
        List of (p_i, n_i) tuples, one per fold.

    Example:
        >>> folds = get_stratified_fold_configuration(p=50, n=100, k=5)
        >>> print(folds)  # [(10, 20), (10, 20), (10, 20), (10, 20), (10, 20)]
    """
    p_div, p_mod = divmod(p, k)
    n_div, n_mod = divmod(n, k)

    folds = []
    for i in range(k):
        p_i = p_div + (1 if i < p_mod else 0)
        n_i = n_div + (1 if i < n_mod else 0)
        folds.append((p_i, n_i))

    return folds


class ConsistencyMixin:
    """
    Mixin class adding consistency testing methods to DConfusion.

    This mixin wraps mlscorecheck (Fazekas & Kovács, 2024) to provide
    consistency testing - verifying if reported scores could mathematically
    result from a given experimental setup.
    """

    @property
    def p(self) -> int:
        """Number of actual positive samples (TP + FN)."""
        if hasattr(self, 'true_positive') and hasattr(self, 'false_negative'):
            return self.true_positive + self.false_negative
        raise AttributeError("Cannot determine p - this may not be a binary confusion matrix")

    @property
    def n(self) -> int:
        """Number of actual negative samples (TN + FP)."""
        if hasattr(self, 'true_negative') and hasattr(self, 'false_positive'):
            return self.true_negative + self.false_positive
        raise AttributeError("Cannot determine n - this may not be a binary confusion matrix")

    def check_reported_scores(
        self,
        scores: Dict[str, float],
        epsilon: Optional[float] = None,
    ) -> ConsistencyResult:
        """
        Check if reported scores are consistent with this confusion matrix's setup.

        This tests whether the reported scores could result from ANY confusion
        matrix with the same p (positives) and n (negatives) as this instance.

        Args:
            scores: Dictionary of score names to reported values.
            epsilon: Numerical uncertainty. If None, inferred from decimal places.

        Returns:
            ConsistencyResult indicating if scores are mathematically possible.

        Example:
            >>> cm = DConfusion(true_positive=45, false_negative=5,
            ...                 false_positive=10, true_negative=40)
            >>> # Check if some published scores are consistent with our setup
            >>> result = cm.check_reported_scores({"acc": 0.85, "sens": 0.90})
            >>> if not result.is_consistent:
            ...     print("Published scores are mathematically impossible!")
        """
        if not self.is_binary:
            raise ValueError("Consistency testing is only supported for binary classification")

        return check_consistency(
            p=self.p,
            n=self.n,
            scores=scores,
            epsilon=epsilon
        )

    def verify_own_scores(
        self,
        score_names: Optional[List[str]] = None,
        decimal_places: int = 4
    ) -> ConsistencyResult:
        """
        Verify that this confusion matrix's own scores pass consistency check.

        This is a sanity check - should always return is_consistent=True
        unless there's a bug somewhere.

        Args:
            score_names: List of score names to verify. If None, uses common scores.
            decimal_places: Round scores to this many decimal places before checking.

        Returns:
            ConsistencyResult (should always be consistent for valid CM).
        """
        if not self.is_binary:
            raise ValueError("Consistency testing is only supported for binary classification")

        if score_names is None:
            score_names = ['accuracy', 'sensitivity', 'specificity']

        # Get our own scores, rounded
        scores = {}
        for name in score_names:
            getter = f'get_{name}'
            if hasattr(self, getter):
                value = getattr(self, getter)()
                scores[name] = round(value, decimal_places)

        return check_consistency(
            p=self.p,
            n=self.n,
            scores=scores,
            epsilon=10 ** (-decimal_places) / 2
        )


# Convenience function to check if mlscorecheck is available
def is_consistency_testing_available() -> bool:
    """Check if consistency testing is available (mlscorecheck installed)."""
    return HAS_MLSCORECHECK


def get_mlscorecheck_version() -> Optional[str]:
    """Get the version of mlscorecheck if installed."""
    return MLSCORECHECK_VERSION
