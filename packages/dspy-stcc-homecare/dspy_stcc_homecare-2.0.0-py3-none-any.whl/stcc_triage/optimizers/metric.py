"""
Validation Metrics for DSPy Optimization.

Metrics that score triage accuracy for BootstrapFewShot optimization.
"""

from typing import Optional

try:
    import dspy
except ImportError:
    raise ImportError("dspy-ai package not installed. Run: uv add dspy-ai")


def protocol_adherence_metric(
    gold: "PatientCase", pred: dspy.Prediction, trace: Optional[str] = None
) -> float:
    """
    Validate triage prediction against gold-standard case.

    Scoring criteria (safety-focused):
    1. Exact match: 1.0
    2. Conservative over-triage: 0.6-0.8 (safer than under-triage)
    3. Missing emergency: 0.0 (catastrophic - patient safety critical)
    4. Under-triage non-emergency: 0.2-0.4 (penalized but not zero)

    Args:
        gold: Gold-standard PatientCase with correct triage_level
        pred: DSPy prediction from agent
        trace: Optional reasoning trace

    Returns:
        float: Score from 0.0 to 1.0
    """
    # Normalize levels to lowercase for comparison
    pred_level = pred.triage_level.lower().strip()
    gold_level = gold.triage_level.lower().strip()

    # Urgency ranking for comparison (higher = more urgent)
    urgency_rank = {
        "emergency": 4,
        "urgent": 3,
        "moderate": 2,
        "home_care": 1,
        "home care": 1,  # Handle space variant
    }

    pred_rank = urgency_rank.get(pred_level, 0)
    gold_rank = urgency_rank.get(gold_level, 0)

    # Exact match - perfect score
    if pred_level == gold_level or pred_level.replace("_", " ") == gold_level.replace(
        "_", " "
    ):
        return 1.0

    # CRITICAL: Missing emergency is unacceptable
    # False negative in emergency detection can cost lives
    if gold_level == "emergency" and pred_level != "emergency":
        return 0.0

    # Over-triage (more conservative) - acceptable with partial credit
    # Better to over-triage than under-triage for patient safety
    if pred_rank > gold_rank:
        gap = pred_rank - gold_rank
        if gap == 1:  # One level up (e.g., moderate → urgent)
            return 0.7
        elif gap == 2:  # Two levels up (e.g., home_care → urgent)
            return 0.5
        else:  # Three levels up (e.g., home_care → emergency)
            return 0.3

    # Under-triage (less conservative) - penalize heavily
    # This is dangerous - patient may not get needed care
    if pred_rank < gold_rank:
        gap = gold_rank - pred_rank
        if gap == 1:  # One level down
            return 0.4
        elif gap == 2:  # Two levels down
            return 0.2
        else:  # Three levels down
            return 0.1

    return 0.3  # Fallback


def red_flag_detection_metric(
    gold: "PatientCase", pred: dspy.Prediction, trace: Optional[str] = None
) -> bool:
    """
    Binary metric: Did agent correctly detect emergency?

    Used for red-flag stress testing.
    Critical for patient safety - missing emergencies is catastrophic.

    Args:
        gold: Gold-standard PatientCase
        pred: DSPy prediction from agent
        trace: Optional reasoning trace

    Returns:
        bool: True if emergency correctly identified, False otherwise
    """
    gold_level = gold.triage_level.lower().strip()
    pred_level = pred.triage_level.lower().strip()

    # If gold standard is emergency, prediction MUST be emergency
    if gold_level == "emergency":
        return pred_level == "emergency"

    # For non-emergencies, any answer is acceptable
    # (we only strictly enforce emergency detection)
    return True


def combined_metric(gold, pred, trace=None) -> float:
    """
    Weighted combination of metrics for optimization.

    Balances overall protocol adherence with critical red-flag detection.

    Weighting:
    - 80% protocol adherence (overall accuracy)
    - 20% red-flag detection (emergency identification)

    Args:
        gold: Gold-standard PatientCase
        pred: DSPy prediction from agent
        trace: Optional reasoning trace

    Returns:
        float: Combined score from 0.0 to 1.0
    """
    adherence_score = protocol_adherence_metric(gold, pred, trace)
    red_flag_score = float(red_flag_detection_metric(gold, pred, trace))

    return 0.8 * adherence_score + 0.2 * red_flag_score


if __name__ == "__main__":
    # Test metrics with mock objects
    print("Testing triage metrics...")

    # Mock objects for testing
    class MockGold:
        def __init__(self, level):
            self.triage_level = level

    class MockPred:
        def __init__(self, level):
            self.triage_level = level

    # Test exact match
    gold = MockGold("emergency")
    pred = MockPred("emergency")
    score = protocol_adherence_metric(gold, pred)
    print(f"Exact match (emergency): {score} (expected 1.0)")
    assert score == 1.0

    # Test missed emergency (catastrophic)
    gold = MockGold("emergency")
    pred = MockPred("urgent")
    score = protocol_adherence_metric(gold, pred)
    print(f"Missed emergency: {score} (expected 0.0)")
    assert score == 0.0

    # Test over-triage (conservative - safer)
    gold = MockGold("urgent")
    pred = MockPred("emergency")
    score = protocol_adherence_metric(gold, pred)
    print(f"Over-triage by 1 level: {score} (expected 0.7)")
    assert score == 0.7

    # Test red-flag detection
    gold = MockGold("emergency")
    pred = MockPred("emergency")
    detected = red_flag_detection_metric(gold, pred)
    print(f"Red flag detected: {detected} (expected True)")
    assert detected is True

    gold = MockGold("emergency")
    pred = MockPred("urgent")
    detected = red_flag_detection_metric(gold, pred)
    print(f"Red flag missed: {detected} (expected False)")
    assert detected is False

    print("\n✓ All metric tests passed!")
