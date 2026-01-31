"""OB/Maternal Nurse Training Cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stcc_triage.datasets.schema import PatientCase

OB_CASES = [
    # Emergency - Suspected labor preterm
    PatientCase(
        case_id=201,
        protocol_category="Pregnancy_Suspected_Labor",
        patient_age=28,
        symptoms="30 weeks pregnant, regular contractions every 5 minutes, vaginal pressure",
        medical_history="First pregnancy",
        triage_level="emergency",
        rationale="Preterm labor at 30 weeks, immediate evaluation needed",
    ),
    # Emergency - Severe vaginal bleeding
    PatientCase(
        case_id=202,
        protocol_category="Pregnancy_Vaginal_Bleeding",
        patient_age=26,
        symptoms="20 weeks pregnant, heavy vaginal bleeding with clots, severe cramping",
        medical_history="Previous miscarriage",
        triage_level="emergency",
        rationale="Significant bleeding in pregnancy, possible placental abruption",
    ),
    # Urgent - Decreased fetal movement
    PatientCase(
        case_id=203,
        protocol_category="Pregnancy_Fetal_Movement_Problems",
        patient_age=32,
        symptoms="36 weeks pregnant, noticed decreased fetal movement for past 6 hours",
        medical_history="Uncomplicated pregnancy",
        triage_level="urgent",
        rationale="Decreased fetal movement requires prompt assessment",
    ),
    # Moderate - Pregnancy nausea
    PatientCase(
        case_id=204,
        protocol_category="Pregnancy_Nausea_and_Vomiting",
        patient_age=25,
        symptoms="8 weeks pregnant, persistent nausea and vomiting, able to keep some fluids down",
        medical_history="First trimester",
        triage_level="moderate",
        rationale="Morning sickness, evaluation and treatment options",
    ),
    # Home care - Breastfeeding questions
    PatientCase(
        case_id=205,
        protocol_category="Breastfeeding_Problems",
        patient_age=30,
        symptoms="2 weeks postpartum, asking about proper latch technique, no fever or severe pain",
        medical_history="First baby",
        triage_level="home_care",
        rationale="Routine breastfeeding education",
    ),
]
