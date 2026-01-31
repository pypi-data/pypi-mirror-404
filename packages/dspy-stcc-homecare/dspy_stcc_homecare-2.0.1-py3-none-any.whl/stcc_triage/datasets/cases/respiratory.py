"""Respiratory Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

RESPIRATORY_CASES = [
    # Emergency
    PatientCase(
        case_id=901,
        protocol_category="Shortness_of_Breath",
        patient_age=58,
        symptoms="58-year-old COPD patient with severe dyspnea, unable to speak full sentences, "
        "O2 sat 82%, using accessory muscles, cyanotic",
        medical_history="COPD, ex-smoker",
        triage_level="emergency",
        rationale="Acute respiratory failure, immediate oxygen and treatment",
    ),
    PatientCase(
        case_id=902,
        protocol_category="Breathing_Problems",
        patient_age=35,
        symptoms="35-year-old asthmatic with severe wheezing, chest tightness, used rescue inhaler 5 times, "
        "no relief, difficulty breathing",
        medical_history="Asthma, multiple hospitalizations",
        triage_level="emergency",
        rationale="Severe asthma exacerbation, status asthmaticus risk",
    ),
    # Urgent
    PatientCase(
        case_id=903,
        protocol_category="Cough",
        patient_age=62,
        symptoms="62-year-old with productive cough with yellow-green sputum, fever 38.8°C, "
        "dyspnea on exertion, history of COPD",
        medical_history="COPD, hypertension",
        triage_level="urgent",
        rationale="Likely COPD exacerbation with infection",
    ),
    PatientCase(
        case_id=904,
        protocol_category="Cough",
        patient_age=45,
        symptoms="45-year-old with persistent dry cough 2 weeks, worsening dyspnea, fever, night sweats",
        medical_history="No chronic respiratory disease",
        triage_level="urgent",
        rationale="Possible pneumonia or TB, needs workup",
    ),
    # Moderate
    PatientCase(
        case_id=905,
        protocol_category="Cough",
        patient_age=40,
        symptoms="40-year-old with cough and mild dyspnea for 5 days, low-grade fever, productive cough",
        medical_history="Healthy, non-smoker",
        triage_level="moderate",
        rationale="Upper respiratory infection or bronchitis",
    ),
    # Home care
    PatientCase(
        case_id=906,
        protocol_category="Cough",
        patient_age=28,
        symptoms="28-year-old with mild cough for 2 days, no fever, no dyspnea, asking about cough remedies",
        medical_history="Healthy",
        triage_level="home_care",
        rationale="Mild URI, home management appropriate",
    ),
]
