"""
Patient Case Schema for Gold-Standard Dataset.

Pydantic models for patient test cases used in validation and optimization.
"""

from pydantic import BaseModel, Field
from typing import Literal


class PatientCase(BaseModel):
    """Single patient case for evaluation and training."""

    case_id: int = Field(description="Unique identifier for this case")
    protocol_category: str = Field(
        description="STCC protocol category (e.g., Chest Pain, Abdominal Pain)"
    )
    patient_age: int = Field(description="Patient age in years")
    symptoms: str = Field(description="Natural language symptom description")
    medical_history: str = Field(description="Relevant medical history")
    triage_level: Literal["emergency", "urgent", "moderate", "home_care"] = Field(
        description="Correct triage level"
    )
    rationale: str = Field(description="Clinical rationale for triage decision")
