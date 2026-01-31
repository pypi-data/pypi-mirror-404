from .DConfusion import DConfusion
from .warnings import (
    ConfusionMatrixWarning,
    WarningSeverity,
    WarningChecker,
    check_comparison_validity
)
from .statistics import (
    StatisticalTestsMixin,
    MetricInferenceMixin
)

# Consistency testing (optional - requires mlscorecheck)
# These are imported conditionally to avoid ImportError if mlscorecheck not installed
try:
    from .consistency import (
        check_consistency,
        check_consistency_kfold,
        enumerate_fold_configurations,
        get_stratified_fold_configuration,
        ConsistencyResult,
        AggregatedConsistencyResult,
        ConsistencyMixin,
        is_consistency_testing_available,
        get_mlscorecheck_version,
    )
    _CONSISTENCY_AVAILABLE = True
except ImportError:
    _CONSISTENCY_AVAILABLE = False

    # Provide stub functions that give helpful error messages
    def check_consistency(*args, **kwargs):
        raise ImportError(
            "Consistency testing requires 'mlscorecheck' by Fazekas & Kovács (2024).\n"
            "Install with: pip install mlscorecheck\n"
            "Or: pip install dconfusion[consistency]"
        )

    def check_consistency_kfold(*args, **kwargs):
        raise ImportError(
            "Consistency testing requires 'mlscorecheck' by Fazekas & Kovács (2024).\n"
            "Install with: pip install mlscorecheck\n"
            "Or: pip install dconfusion[consistency]"
        )

    def enumerate_fold_configurations(*args, **kwargs):
        raise ImportError(
            "Fold enumeration requires 'mlscorecheck' by Fazekas & Kovács (2024).\n"
            "Install with: pip install mlscorecheck\n"
            "Or: pip install dconfusion[consistency]"
        )

    def get_stratified_fold_configuration(p, n, k):
        """Get stratified fold configuration (no mlscorecheck needed)."""
        p_div, p_mod = divmod(p, k)
        n_div, n_mod = divmod(n, k)
        folds = []
        for i in range(k):
            p_i = p_div + (1 if i < p_mod else 0)
            n_i = n_div + (1 if i < n_mod else 0)
            folds.append((p_i, n_i))
        return folds

    def is_consistency_testing_available():
        return False

    def get_mlscorecheck_version():
        return None

    ConsistencyResult = None
    AggregatedConsistencyResult = None
    ConsistencyMixin = None


__all__ = [
    # Core
    'DConfusion',
    # Warnings
    'ConfusionMatrixWarning',
    'WarningSeverity',
    'WarningChecker',
    'check_comparison_validity',
    # Statistics
    'StatisticalTestsMixin',
    'MetricInferenceMixin',
    # Consistency testing (mlscorecheck wrapper)
    'check_consistency',
    'check_consistency_kfold',
    'enumerate_fold_configurations',
    'get_stratified_fold_configuration',
    'ConsistencyResult',
    'AggregatedConsistencyResult',
    'ConsistencyMixin',
    'is_consistency_testing_available',
    'get_mlscorecheck_version',
]