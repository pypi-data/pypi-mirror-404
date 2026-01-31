"""
STCC Triage Agent - A DSPy Extension for Medical Triage.

Professional medical triage system with specialized nurses powered by DSPy and DeepSeek.
"""

from stcc_triage.core.agent import STCCTriageAgent
from stcc_triage.core.signatures import TriageSignature, FollowUpSignature
from stcc_triage.nurses.roles import NurseRole
from stcc_triage.nurses.specialized import (
    WoundCareNurse,
    OBNurse,
    PediatricNurse,
    NeuroNurse,
    GINurse,
    RespiratoryNurse,
    MentalHealthNurse,
    CHFNurse,
    EDNurse,
    PreOpNurse,
    GeneralNurse,
)
from stcc_triage.optimizers.compiler import optimize_nurse, load_compiled_nurse
from stcc_triage.datasets.generator import generate_all_specialized_datasets
from stcc_triage.protocols.parser import parse_all_protocols

__all__ = [
    # Core
    "STCCTriageAgent",
    "TriageSignature",
    "FollowUpSignature",
    # Nurse roles
    "NurseRole",
    # Specialized nurses
    "WoundCareNurse",
    "OBNurse",
    "PediatricNurse",
    "NeuroNurse",
    "GINurse",
    "RespiratoryNurse",
    "MentalHealthNurse",
    "CHFNurse",
    "EDNurse",
    "PreOpNurse",
    "GeneralNurse",
    # Optimization
    "optimize_nurse",
    "load_compiled_nurse",
    # Data generation
    "generate_all_specialized_datasets",
    # Protocol parsing
    "parse_all_protocols",
]

__version__ = "2.0.0"
