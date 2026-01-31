"""Wound Care Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

WOUND_CARE_CASES = [
    # Emergency - Severe bleeding
    PatientCase(
        case_id=101,
        protocol_category="Bleeding_Severe",
        patient_age=35,
        symptoms="Deep laceration to forearm, bright red blood spurting, unable to control with direct pressure",
        medical_history="No bleeding disorders",
        triage_level="emergency",
        rationale="Arterial bleeding, life-threatening hemorrhage",
    ),
    # Emergency - Major burn
    PatientCase(
        case_id=102,
        protocol_category="Burns_Thermal",
        patient_age=45,
        symptoms="Second-degree burns covering 20% body surface, severe pain, blistering on chest and arms",
        medical_history="House fire injury",
        triage_level="emergency",
        rationale="Major burn requiring immediate care, fluid resuscitation needed",
    ),
    # Urgent - Deep wound
    PatientCase(
        case_id=103,
        protocol_category="Laceration",
        patient_age=28,
        symptoms="4cm laceration on leg from broken glass, bleeding controlled, but deep, gaping wound",
        medical_history="Tetanus shot 3 years ago",
        triage_level="urgent",
        rationale="Deep laceration requiring suturing, evaluation within hours",
    ),
    # Moderate - Minor burn
    PatientCase(
        case_id=104,
        protocol_category="Burns_Thermal",
        patient_age=32,
        symptoms="Small first-degree burn on hand from cooking, red and painful, no blistering",
        medical_history="None",
        triage_level="moderate",
        rationale="Minor burn, outpatient wound care",
    ),
    # Home care - Minor abrasion
    PatientCase(
        case_id=105,
        protocol_category="Abrasions",
        patient_age=25,
        symptoms="Scraped knee from bicycle fall, cleaned and covered, no active bleeding",
        medical_history="Up to date on tetanus",
        triage_level="home_care",
        rationale="Minor abrasion, home wound care appropriate",
    ),
]
