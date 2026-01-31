"""PreOp (Pre-Operative) Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

PREOP_CASES = [
    # Emergency (contraindication found)
    PatientCase(
        case_id=801,
        protocol_category="Fever",
        patient_age=45,
        symptoms="45-year-old scheduled for surgery tomorrow, now has fever 39°C, severe cough, "
        "productive sputum, shortness of breath",
        medical_history="Scheduled for elective surgery",
        triage_level="emergency",
        rationale="Active infection, surgery contraindicated, needs immediate treatment",
    ),
    PatientCase(
        case_id=802,
        protocol_category="Chest_Pain",
        patient_age=62,
        symptoms="62-year-old preop patient with new onset chest pain radiating to left arm, "
        "diaphoresis, scheduled for hip surgery in 2 days",
        medical_history="Hypertension, scheduled for hip replacement",
        triage_level="emergency",
        rationale="Acute cardiac event, immediate evaluation needed",
    ),
    # Urgent
    PatientCase(
        case_id=803,
        protocol_category="Hypertension",
        patient_age=58,
        symptoms="58-year-old preop assessment, blood pressure 180/110, history of hypertension, "
        "scheduled for surgery in 5 days",
        medical_history="Poorly controlled hypertension",
        triage_level="urgent",
        rationale="Uncontrolled hypertension, needs optimization before surgery",
    ),
    PatientCase(
        case_id=804,
        protocol_category="Bleeding_Risk",
        patient_age=50,
        symptoms="50-year-old preop, reports taking aspirin and clopidogrel, "
        "orthopedic surgery scheduled in 3 days, no one told patient to stop",
        medical_history="Cardiac stents, on antiplatelet therapy",
        triage_level="urgent",
        rationale="Bleeding risk, medication adjustment needed urgently",
    ),
    # Moderate
    PatientCase(
        case_id=805,
        protocol_category="Anxiety",
        patient_age=48,
        symptoms="48-year-old preop assessment, mild anxiety about anesthesia, "
        "wants to discuss concerns, surgery in 1 week",
        medical_history="No significant medical history",
        triage_level="moderate",
        rationale="Routine preop anxiety, counseling needed",
    ),
    # Home care
    PatientCase(
        case_id=806,
        protocol_category="Preop_Education",
        patient_age=40,
        symptoms="40-year-old preop patient, asking about fasting instructions for surgery next week",
        medical_history="Healthy, scheduled for elective surgery",
        triage_level="home_care",
        rationale="Routine preop education question",
    ),
]
