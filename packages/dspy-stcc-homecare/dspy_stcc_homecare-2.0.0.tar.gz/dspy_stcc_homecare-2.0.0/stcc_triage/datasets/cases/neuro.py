"""Neuro Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

NEURO_CASES = [
    # Emergency - Suspected stroke
    PatientCase(
        case_id=301,
        protocol_category="Stroke_Suspected",
        patient_age=68,
        symptoms="Sudden right-sided weakness, facial droop, slurred speech, started 30 minutes ago",
        medical_history="Hypertension, atrial fibrillation",
        triage_level="emergency",
        rationale="Acute stroke symptoms, immediate evaluation for thrombolytics",
    ),
    # Emergency - Active seizure
    PatientCase(
        case_id=302,
        protocol_category="Seizure",
        patient_age=45,
        symptoms="Generalized tonic-clonic seizure lasting >5 minutes, unresponsive",
        medical_history="Epilepsy, missed medication",
        triage_level="emergency",
        rationale="Status epilepticus, immediate intervention needed",
    ),
    # Urgent - Severe headache
    PatientCase(
        case_id=303,
        protocol_category="Headache",
        patient_age=42,
        symptoms="Worst headache of life, sudden onset, photophobia, stiff neck",
        medical_history="No previous severe headaches",
        triage_level="urgent",
        rationale="Possible subarachnoid hemorrhage, urgent evaluation",
    ),
    # Moderate - Post-seizure
    PatientCase(
        case_id=304,
        protocol_category="Seizure",
        patient_age=35,
        symptoms="Brief seizure 2 hours ago, now alert and oriented, taking anti-epileptics",
        medical_history="Known epilepsy, well-controlled",
        triage_level="moderate",
        rationale="Post-ictal, stable, needs evaluation",
    ),
    # Home care - Mild headache
    PatientCase(
        case_id=305,
        protocol_category="Headache",
        patient_age=30,
        symptoms="Tension headache for 1 day, responds to ibuprofen, no neurological symptoms",
        medical_history="Frequent tension headaches",
        triage_level="home_care",
        rationale="Benign tension headache, home management",
    ),
]
