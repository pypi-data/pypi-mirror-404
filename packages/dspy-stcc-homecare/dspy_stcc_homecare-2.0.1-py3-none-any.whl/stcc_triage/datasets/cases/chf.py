"""CHF (Congestive Heart Failure) Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

CHF_CASES = [
    # Emergency
    PatientCase(
        case_id=1,
        protocol_category="Shortness of Breath",
        patient_age=65,
        symptoms="Severe shortness of breath at rest, orthopnea, frothy pink sputum, bilateral leg edema",
        medical_history="History of CHF, hypertension, diabetes",
        triage_level="emergency",
        rationale="Acute pulmonary edema, immediate intervention needed",
    ),
    PatientCase(
        case_id=2,
        protocol_category="Chest Pain",
        patient_age=72,
        symptoms="Chest pain, severe dyspnea, cold extremities, blood pressure 85/50, heart rate 120",
        medical_history="CHF, previous MI",
        triage_level="emergency",
        rationale="Cardiogenic shock, critical instability",
    ),
    # Urgent
    PatientCase(
        case_id=3,
        protocol_category="Shortness of Breath",
        patient_age=68,
        symptoms="Weight gain 5kg in 2 days, increasing dyspnea on exertion, ankle swelling worsening",
        medical_history="Known CHF on diuretics",
        triage_level="urgent",
        rationale="CHF exacerbation, needs medical evaluation within hours",
    ),
    PatientCase(
        case_id=4,
        protocol_category="Shortness of Breath",
        patient_age=58,
        symptoms="Missed diuretic doses for 3 days, now with dyspnea, orthopnea, leg swelling",
        medical_history="CHF, medication non-compliance",
        triage_level="urgent",
        rationale="Fluid overload from medication non-compliance",
    ),
    # Moderate
    PatientCase(
        case_id=5,
        protocol_category="Swelling",
        patient_age=55,
        symptoms="Mild increase in ankle swelling, slight increase in dyspnea with exertion",
        medical_history="Controlled CHF on medications",
        triage_level="moderate",
        rationale="Early signs of decompensation, outpatient evaluation needed",
    ),
    # Home care
    PatientCase(
        case_id=6,
        protocol_category="CHF Management",
        patient_age=60,
        symptoms="Stable, taking medications regularly, asking about dietary sodium guidelines",
        medical_history="Stable CHF",
        triage_level="home_care",
        rationale="Routine CHF management question, education needed",
    ),
]
