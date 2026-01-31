"""Pediatric Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

PEDIATRIC_CASES = [
    # Emergency
    PatientCase(
        case_id=601,
        protocol_category="Fever_Child",
        patient_age=1,
        symptoms="6-month-old with fever 40°C, lethargic, poor feeding, weak cry, fontanelle bulging",
        medical_history="Healthy infant, no chronic conditions",
        triage_level="emergency",
        rationale="Infant with concerning signs, possible meningitis or sepsis",
    ),
    PatientCase(
        case_id=602,
        protocol_category="Breathing_Problems_Child",
        patient_age=2,
        symptoms="2-year-old with severe difficulty breathing, retractions, nasal flaring, "
        "O2 sat 88% on room air, wheezing",
        medical_history="History of asthma",
        triage_level="emergency",
        rationale="Respiratory distress, immediate intervention needed",
    ),
    # Urgent
    PatientCase(
        case_id=603,
        protocol_category="Ear_Pain",
        patient_age=4,
        symptoms="4-year-old with high fever 39.5°C for 2 days, pulling at ear, crying, not eating well",
        medical_history="Previous ear infections",
        triage_level="urgent",
        rationale="Likely otitis media, needs evaluation and treatment",
    ),
    PatientCase(
        case_id=604,
        protocol_category="Vomiting_Child",
        patient_age=2,
        symptoms="18-month-old with vomiting and diarrhea for 2 days, decreased wet diapers, "
        "dry lips, lethargic",
        medical_history="No chronic conditions",
        triage_level="urgent",
        rationale="Dehydration signs, needs assessment",
    ),
    # Moderate
    PatientCase(
        case_id=605,
        protocol_category="Fever_Child",
        patient_age=5,
        symptoms="5-year-old with fever 38.5°C, runny nose, cough for 3 days, eating and drinking okay",
        medical_history="Healthy child",
        triage_level="moderate",
        rationale="Upper respiratory infection, routine evaluation",
    ),
    # Home care
    PatientCase(
        case_id=606,
        protocol_category="Cough",
        patient_age=3,
        symptoms="3-year-old with mild runny nose, no fever, eating and playing normally",
        medical_history="Healthy child",
        triage_level="home_care",
        rationale="Mild URI, supportive care at home",
    ),
]
