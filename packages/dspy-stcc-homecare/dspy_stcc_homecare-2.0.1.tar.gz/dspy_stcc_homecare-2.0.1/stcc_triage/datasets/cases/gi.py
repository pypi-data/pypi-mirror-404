"""GI Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

GI_CASES = [
    # Emergency - Severe abdominal pain with peritonitis
    PatientCase(
        case_id=401,
        protocol_category="Abdominal_Pain_Adult",
        patient_age=45,
        symptoms="Severe abdominal pain with rigid abdomen, fever 39°C, rebound tenderness, vomiting",
        medical_history="Appendectomy 10 years ago",
        triage_level="emergency",
        rationale="Acute abdomen with peritonitis signs, surgical emergency",
    ),
    # Urgent - Persistent vomiting with dehydration
    PatientCase(
        case_id=402,
        protocol_category="Vomiting_Adult",
        patient_age=38,
        symptoms="Vomiting for 24 hours, unable to keep fluids down, dizzy when standing, dry mouth",
        medical_history="None",
        triage_level="urgent",
        rationale="Dehydration from persistent vomiting, needs IV fluids",
    ),
    # Urgent - Rectal bleeding
    PatientCase(
        case_id=403,
        protocol_category="Rectal_Bleeding",
        patient_age=55,
        symptoms="Bright red blood in stool, moderate amount, ongoing for 2 days, fatigue",
        medical_history="No previous GI bleeding",
        triage_level="urgent",
        rationale="Active GI bleeding requires prompt evaluation",
    ),
    # Moderate - Abdominal pain
    PatientCase(
        case_id=404,
        protocol_category="Abdominal_Pain_Adult",
        patient_age=35,
        symptoms="Cramping abdominal pain with diarrhea for 2 days, no fever, tolerating fluids",
        medical_history="None",
        triage_level="moderate",
        rationale="Likely gastroenteritis, evaluation and supportive care",
    ),
    # Home care - Mild indigestion
    PatientCase(
        case_id=405,
        protocol_category="Indigestion",
        patient_age=40,
        symptoms="Mild heartburn after spicy meal, responds to antacids",
        medical_history="Occasional reflux",
        triage_level="home_care",
        rationale="Simple indigestion, home management appropriate",
    ),
]
