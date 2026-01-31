"""
Specialized Nurse Classes.

Convenience wrapper classes for specialized nurse agents.
"""

from stcc_triage.core.agent import STCCTriageAgent
from stcc_triage.nurses.roles import NurseRole
from stcc_triage.optimizers.compiler import load_compiled_nurse


class SpecializedNurse(STCCTriageAgent):
    """Base class for specialized nurses with compiled agents."""

    def __init__(self, role: NurseRole):
        """
        Initialize a specialized nurse.

        Args:
            role: The nurse role specialization

        Raises:
            FileNotFoundError: If compiled agent not found for this role
        """
        super().__init__()
        self.role = role
        self.load_compiled(role)

    def load_compiled(self, role: NurseRole):
        """
        Load pre-compiled optimization for this role.

        Args:
            role: The nurse role

        Raises:
            FileNotFoundError: If compiled agent not found
        """
        try:
            compiled_module = load_compiled_nurse(role)
            self.triage_module = compiled_module
        except FileNotFoundError:
            print(
                f"\nWarning: No compiled agent found for {role.value}\n"
                f"Run: stcc-optimize --role {role.value}\n"
                f"Using baseline agent for now."
            )


class WoundCareNurse(SpecializedNurse):
    """Wound Care & Trauma Specialist."""

    def __init__(self):
        super().__init__(NurseRole.WOUND_CARE_NURSE)


class OBNurse(SpecializedNurse):
    """OB/Maternal Health Specialist."""

    def __init__(self):
        super().__init__(NurseRole.OB_NURSE)


class PediatricNurse(SpecializedNurse):
    """Pediatric & Child Health Specialist."""

    def __init__(self):
        super().__init__(NurseRole.PEDIATRIC_NURSE)


class NeuroNurse(SpecializedNurse):
    """Neurological Specialist."""

    def __init__(self):
        super().__init__(NurseRole.NEURO_NURSE)


class GINurse(SpecializedNurse):
    """Gastrointestinal Specialist."""

    def __init__(self):
        super().__init__(NurseRole.GI_NURSE)


class RespiratoryNurse(SpecializedNurse):
    """Respiratory Specialist."""

    def __init__(self):
        super().__init__(NurseRole.RESPIRATORY_NURSE)


class MentalHealthNurse(SpecializedNurse):
    """Mental Health & Behavioral Specialist."""

    def __init__(self):
        super().__init__(NurseRole.MENTAL_HEALTH_NURSE)


class CHFNurse(SpecializedNurse):
    """Congestive Heart Failure Specialist."""

    def __init__(self):
        super().__init__(NurseRole.CHF_NURSE)


class EDNurse(SpecializedNurse):
    """Emergency Department Specialist."""

    def __init__(self):
        super().__init__(NurseRole.ED_NURSE)


class PreOpNurse(SpecializedNurse):
    """Pre-operative Assessment Specialist."""

    def __init__(self):
        super().__init__(NurseRole.PREOP_NURSE)


class GeneralNurse(SpecializedNurse):
    """General Triage Nurse (all specialties)."""

    def __init__(self):
        super().__init__(NurseRole.GENERAL_NURSE)
