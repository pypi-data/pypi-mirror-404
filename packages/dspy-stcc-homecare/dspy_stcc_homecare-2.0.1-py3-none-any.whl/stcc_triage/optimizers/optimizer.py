"""
DSPy BootstrapFewShot Optimizer for Triage Agent.

Optimizes the triage agent using BootstrapFewShot with gold-standard dataset.
"""

try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot
except ImportError:
    raise ImportError("dspy-ai package not installed. Run: uv add dspy-ai")

from stcc_triage.optimizers.metric import combined_metric, protocol_adherence_metric


def get_optimizer(
    max_bootstrapped_demos: int = 8,
    max_labeled_demos: int = 4,
    max_rounds: int = 1,
    max_errors: int = 5,
) -> BootstrapFewShot:
    """
    Get configured BootstrapFewShot optimizer for specialized compilation.

    Args:
        max_bootstrapped_demos: Teacher-generated examples (default: 8)
        max_labeled_demos: Random samples from trainset (default: 4)
        max_rounds: Optimization rounds (default: 1)
        max_errors: Max errors allowed during bootstrapping (default: 5)

    Returns:
        Configured BootstrapFewShot teleprompter
    """
    return BootstrapFewShot(
        metric=protocol_adherence_metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
        max_rounds=max_rounds,
        max_errors=max_errors,
    )
