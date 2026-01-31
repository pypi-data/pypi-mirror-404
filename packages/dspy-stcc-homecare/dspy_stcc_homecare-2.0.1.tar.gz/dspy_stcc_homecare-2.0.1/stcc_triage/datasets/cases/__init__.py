"""
Case Data Package.

Contains domain-specific patient cases for each nurse specialization.
Each module contains training cases for specialized triage agent optimization.
"""

from .chf import CHF_CASES
from .preop import PREOP_CASES
from .ed import ED_CASES
from .pediatric import PEDIATRIC_CASES
from .wound_care import WOUND_CARE_CASES
from .ob import OB_CASES
from .neuro import NEURO_CASES
from .gi import GI_CASES
from .mental_health import MENTAL_HEALTH_CASES
from .respiratory import RESPIRATORY_CASES

__all__ = [
    "CHF_CASES",
    "PREOP_CASES",
    "ED_CASES",
    "PEDIATRIC_CASES",
    "WOUND_CARE_CASES",
    "OB_CASES",
    "NEURO_CASES",
    "GI_CASES",
    "MENTAL_HEALTH_CASES",
    "RESPIRATORY_CASES",
]
