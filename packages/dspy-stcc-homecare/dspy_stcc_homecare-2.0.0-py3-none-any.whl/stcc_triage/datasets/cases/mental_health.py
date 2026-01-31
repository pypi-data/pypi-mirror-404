"""Mental Health Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

MENTAL_HEALTH_CASES = [
    # Emergency - Suicide attempt
    PatientCase(
        case_id=501,
        protocol_category="Suicide_Attempt_Threat",
        patient_age=32,
        symptoms="Took overdose of pills 30 minutes ago, expressing desire to die, lethargic",
        medical_history="Depression, previous attempts",
        triage_level="emergency",
        rationale="Active suicide attempt, immediate medical and psychiatric care",
    ),
    # Emergency - Acute psychosis
    PatientCase(
        case_id=502,
        protocol_category="Altered_Mental_Status_AMS",
        patient_age=28,
        symptoms="Hallucinating, agitated, threatening harm to others, not oriented",
        medical_history="Schizophrenia, medication non-compliance",
        triage_level="emergency",
        rationale="Acute psychotic episode with danger to self/others",
    ),
    # Urgent - Severe anxiety/panic
    PatientCase(
        case_id=503,
        protocol_category="Anxiety",
        patient_age=35,
        symptoms="Severe panic attack for 1 hour, chest pain, hyperventilating, can't calm down",
        medical_history="Panic disorder",
        triage_level="urgent",
        rationale="Severe panic attack, needs medical evaluation and crisis intervention",
    ),
    # Moderate - Anxiety
    PatientCase(
        case_id=504,
        protocol_category="Anxiety",
        patient_age=40,
        symptoms="Increased anxiety for 2 weeks, difficulty sleeping, worried about work stress",
        medical_history="No psychiatric history",
        triage_level="moderate",
        rationale="New onset anxiety, needs evaluation and counseling",
    ),
    # Home care - Mild stress
    PatientCase(
        case_id=505,
        protocol_category="Anxiety",
        patient_age=30,
        symptoms="Mild stress from life changes, sleeping okay, functioning normally, seeking advice",
        medical_history="None",
        triage_level="home_care",
        rationale="Normal stress response, education and coping strategies",
    ),
]
