"""
Nurse Role Specializations.

Defines different nurse roles with their clinical focus areas
for domain-specific agent optimization.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel


class NurseRole(str, Enum):
    """Specialized nurse role types."""

    # TOP protocol categories (by volume)
    WOUND_CARE_NURSE = "wound_care_nurse"  # Wounds/Trauma - 24 protocols!
    OB_NURSE = "ob_nurse"  # Pregnancy/Maternal - 13 protocols!
    PEDIATRIC_NURSE = "pediatric_nurse"  # Children - 12 protocols

    # Major specialty areas
    NEURO_NURSE = "neuro_nurse"  # Neurological - 7 protocols
    GI_NURSE = "gi_nurse"  # GI/Digestive - 6 protocols
    RESPIRATORY_NURSE = "respiratory_nurse"  # Respiratory - 6 protocols
    MENTAL_HEALTH_NURSE = "mental_health_nurse"  # Mental Health - 5 protocols

    # Cardiac specialization
    CHF_NURSE = "chf_nurse"  # Congestive Heart Failure - 4 protocols

    # Emergency specialization
    ED_NURSE = "ed_nurse"  # Emergency Department

    # Surgical specialization
    PREOP_NURSE = "preop_nurse"  # Pre-operative assessment

    # General
    GENERAL_NURSE = "general_nurse"  # General triage


class NurseSpecialization(BaseModel):
    """Configuration for a specialized nurse role."""

    role: NurseRole
    display_name: str
    description: str
    focus_symptoms: List[str]  # Symptom keywords to prioritize
    focus_protocols: List[str]  # Protocol categories to focus on
    min_training_cases: int = 16  # Minimum cases needed for optimization


# Define specializations
NURSE_SPECIALIZATIONS = {
    # TOP VOLUME CATEGORIES
    NurseRole.WOUND_CARE_NURSE: NurseSpecialization(
        role=NurseRole.WOUND_CARE_NURSE,
        display_name="Wound Care Nurse",
        description="Trauma and wound specialist - lacerations, burns, bleeding, wound healing",
        focus_symptoms=[
            "laceration",
            "bleeding",
            "burn",
            "wound",
            "cut",
            "abrasion",
            "bruising",
            "trauma",
            "injury",
            "puncture wound",
        ],
        focus_protocols=[
            "Laceration",
            "Bleeding_Severe",
            "Burns_Thermal",
            "Burns_Chemical",
            "Burns_Electrical",
            "Wound_Healing_and_Infection",
            "Abrasions",
            "Puncture_Wound",
            "Bruising",
        ],
        min_training_cases=16,
    ),
    NurseRole.OB_NURSE: NurseSpecialization(
        role=NurseRole.OB_NURSE,
        display_name="OB/Maternal Nurse",
        description="Pregnancy and maternal health specialist - prenatal, labor, postpartum",
        focus_symptoms=[
            "pregnancy",
            "contractions",
            "vaginal bleeding",
            "fetal movement",
            "labor",
            "postpartum",
            "breastfeeding",
            "pregnancy nausea",
            "pregnancy hypertension",
        ],
        focus_protocols=[
            "Pregnancy_Suspected_Labor",
            "Pregnancy_Vaginal_Bleeding",
            "Pregnancy_Problems",
            "Pregnancy_Fetal_Movement_Problems",
            "Postpartum_Problems",
            "Breastfeeding_Problems",
            "Pregnancy_Nausea_and_Vomiting",
            "Pregnancy_Hypertension",
        ],
        min_training_cases=16,
    ),
    NurseRole.NEURO_NURSE: NurseSpecialization(
        role=NurseRole.NEURO_NURSE,
        display_name="Neuro Nurse",
        description="Neurological specialist - stroke, seizure, headache, altered mental status",
        focus_symptoms=[
            "stroke",
            "seizure",
            "headache",
            "confusion",
            "altered mental status",
            "numbness",
            "tingling",
            "weakness",
            "neurologic symptoms",
            "speech difficulty",
        ],
        focus_protocols=[
            "Stroke_Suspected",
            "Seizure",
            "Headache",
            "Altered_Mental_Status_AMS",
            "Confusion",
            "Neurologic_Symptoms",
            "Numbness_and_Tingling",
        ],
        min_training_cases=12,
    ),
    NurseRole.GI_NURSE: NurseSpecialization(
        role=NurseRole.GI_NURSE,
        display_name="GI Nurse",
        description="Gastrointestinal specialist - abdominal pain, vomiting, diarrhea, GI symptoms",
        focus_symptoms=[
            "abdominal pain",
            "vomiting",
            "diarrhea",
            "nausea",
            "constipation",
            "rectal bleeding",
            "indigestion",
            "appetite loss",
        ],
        focus_protocols=[
            "Abdominal_Pain_Adult",
            "Abdominal_Pain_Child",
            "Vomiting_Adult",
            "Vomiting_Child",
            "Diarrhea",
            "Rectal_Bleeding",
            "Constipation",
            "Indigestion",
        ],
        min_training_cases=12,
    ),
    NurseRole.MENTAL_HEALTH_NURSE: NurseSpecialization(
        role=NurseRole.MENTAL_HEALTH_NURSE,
        display_name="Mental Health Nurse",
        description="Behavioral health specialist - anxiety, depression, suicide risk, substance abuse",
        focus_symptoms=[
            "anxiety",
            "depression",
            "suicide",
            "substance abuse",
            "alcohol problems",
            "behavioral",
            "panic",
            "mental health crisis",
        ],
        focus_protocols=[
            "Anxiety",
            "Depression",
            "Suicide_Attempt_Threat",
            "Substance_Abuse_Use_or_Exposure",
            "Alcohol_Problems",
        ],
        min_training_cases=12,
    ),
    NurseRole.CHF_NURSE: NurseSpecialization(
        role=NurseRole.CHF_NURSE,
        display_name="CHF Nurse",
        description="Congestive Heart Failure specialist - cardiac symptoms, fluid overload, dyspnea",
        focus_symptoms=[
            "chest pain",
            "shortness of breath",
            "dyspnea",
            "edema",
            "swelling",
            "heart palpitations",
            "fatigue",
            "orthopnea",
            "paroxysmal nocturnal dyspnea",
        ],
        focus_protocols=[
            "Chest Pain",
            "Shortness of Breath",
            "Swelling",
            "Heart Palpitations",
        ],
        min_training_cases=12,
    ),
    NurseRole.PREOP_NURSE: NurseSpecialization(
        role=NurseRole.PREOP_NURSE,
        display_name="PreOp Nurse",
        description="Pre-operative assessment specialist - surgical risk, medication review, clearance",
        focus_symptoms=[
            "surgical history",
            "medication review",
            "bleeding risk",
            "anesthesia concerns",
            "cardiac clearance",
            "infection",
            "fever",
        ],
        focus_protocols=[
            "Fever",
            "Chest Pain",
            "Bleeding",
            "Abdominal Pain",
        ],
        min_training_cases=12,
    ),
    NurseRole.ED_NURSE: NurseSpecialization(
        role=NurseRole.ED_NURSE,
        display_name="ED Nurse",
        description="Emergency Department specialist - acute trauma, emergencies, rapid assessment",
        focus_symptoms=[
            "trauma",
            "severe pain",
            "bleeding",
            "unconscious",
            "seizure",
            "chest pain",
            "difficulty breathing",
            "severe headache",
            "abdominal pain",
        ],
        focus_protocols=[
            "Chest Pain",
            "Head Injury",
            "Abdominal Pain",
            "Bleeding",
            "Breathing Problems",
            "Seizures",
        ],
        min_training_cases=16,
    ),
    NurseRole.PEDIATRIC_NURSE: NurseSpecialization(
        role=NurseRole.PEDIATRIC_NURSE,
        display_name="Pediatric Nurse",
        description="Child health specialist - infant/child symptoms, developmental concerns",
        focus_symptoms=[
            "fever in child",
            "infant crying",
            "rash",
            "vomiting",
            "diarrhea",
            "cough in child",
            "ear pain",
            "difficulty breathing in child",
        ],
        focus_protocols=[
            "Fever - Child",
            "Cough",
            "Vomiting",
            "Diarrhea",
            "Rash",
            "Ear Pain",
        ],
        min_training_cases=12,
    ),
    NurseRole.RESPIRATORY_NURSE: NurseSpecialization(
        role=NurseRole.RESPIRATORY_NURSE,
        display_name="Respiratory Nurse",
        description="Respiratory specialist - breathing issues, asthma, COPD, pneumonia",
        focus_symptoms=[
            "shortness of breath",
            "cough",
            "wheezing",
            "chest tightness",
            "difficulty breathing",
            "hypoxia",
            "respiratory distress",
        ],
        focus_protocols=[
            "Shortness of Breath",
            "Cough",
            "Chest Pain",
            "Breathing Problems",
        ],
        min_training_cases=12,
    ),
    NurseRole.GENERAL_NURSE: NurseSpecialization(
        role=NurseRole.GENERAL_NURSE,
        display_name="General Nurse",
        description="General triage nurse - broad coverage across all symptom types",
        focus_symptoms=[],  # No specific focus
        focus_protocols=[],  # All protocols
        min_training_cases=32,
    ),
}


def get_specialization(role: NurseRole) -> NurseSpecialization:
    """
    Get specialization configuration for a nurse role.

    Args:
        role: The nurse role

    Returns:
        NurseSpecialization configuration
    """
    return NURSE_SPECIALIZATIONS[role]


def list_available_roles() -> List[NurseRole]:
    """List all available nurse roles."""
    return list(NURSE_SPECIALIZATIONS.keys())
