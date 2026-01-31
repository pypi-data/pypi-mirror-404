"""ED (Emergency Department) Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

ED_CASES = [
    # Emergency
    PatientCase(
        case_id=701,
        protocol_category="Head_Injury",
        patient_age=35,
        symptoms="35-year-old motor vehicle accident, unresponsive, GCS 6, "
        "obvious head trauma, hypotensive",
        medical_history="No prior medical history",
        triage_level="emergency",
        rationale="Severe trauma, immediate resuscitation needed",
    ),
    PatientCase(
        case_id=702,
        protocol_category="Headache",
        patient_age=28,
        symptoms="28-year-old with sudden severe headache 'worst of my life', stiff neck, "
        "photophobia, vomiting",
        medical_history="No history of migraines",
        triage_level="emergency",
        rationale="Possible subarachnoid hemorrhage, immediate imaging needed",
    ),
    PatientCase(
        case_id=703,
        protocol_category="Chest_Pain",
        patient_age=55,
        symptoms="55-year-old with crushing substernal chest pain 30 minutes, "
        "radiation to jaw, diaphoresis, nausea",
        medical_history="Hypertension, smoker",
        triage_level="emergency",
        rationale="STEMI protocol, immediate cath lab activation",
    ),
    PatientCase(
        case_id=704,
        protocol_category="Fall_Injury",
        patient_age=70,
        symptoms="70-year-old fell at home, severe hip pain, unable to walk, leg shortened and rotated",
        medical_history="Osteoporosis, hypertension",
        triage_level="emergency",
        rationale="Hip fracture, pain management and surgical evaluation",
    ),
    # Urgent
    PatientCase(
        case_id=705,
        protocol_category="Abdominal_Pain_Adult",
        patient_age=42,
        symptoms="42-year-old with severe abdominal pain 6 hours, right lower quadrant, "
        "fever 38.5°C, rebound tenderness",
        medical_history="No prior abdominal surgeries",
        triage_level="urgent",
        rationale="Possible appendicitis, surgical evaluation needed",
    ),
    PatientCase(
        case_id=706,
        protocol_category="Fever_Child",
        patient_age=8,
        symptoms="8-year-old with high fever 40°C, severe headache, neck stiffness, petechial rash",
        medical_history="Up to date on vaccinations",
        triage_level="urgent",
        rationale="Possible meningitis, urgent workup needed",
    ),
    # Moderate
    PatientCase(
        case_id=707,
        protocol_category="Ankle_Injury",
        patient_age=32,
        symptoms="32-year-old with ankle sprain after sports, moderate swelling, able to bear some weight",
        medical_history="Active, no prior injuries",
        triage_level="moderate",
        rationale="Likely sprain, X-ray and assessment needed",
    ),
    # Home care
    PatientCase(
        case_id=708,
        protocol_category="Abrasions",
        patient_age=25,
        symptoms="25-year-old with minor abrasion on arm, cleaned at home, asking about infection signs",
        medical_history="Healthy, tetanus up to date",
        triage_level="home_care",
        rationale="Minor injury, education on wound care",
    ),
]
