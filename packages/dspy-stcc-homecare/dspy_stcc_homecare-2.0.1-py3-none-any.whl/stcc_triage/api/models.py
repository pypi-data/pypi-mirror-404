"""
API Request and Response Models.

Pydantic models for FastAPI endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class TriageRequest(BaseModel):
    """Request model for triage endpoint."""

    symptoms: str = Field(
        ...,
        description="Patient symptom description",
        example="55-year-old with severe chest pain and shortness of breath"
    )
    conversation_history: Optional[List[str]] = Field(
        default=None,
        description="Previous patient messages for context"
    )
    nurse_role: Optional[str] = Field(
        default=None,
        description="Specialized nurse role (e.g., 'wound_care_nurse', 'ob_nurse')"
    )


class TriageResponse(BaseModel):
    """Response model for triage endpoint."""

    triage_level: str = Field(
        ...,
        description="Triage urgency level: Emergency, Urgent, Moderate, or Home Care"
    )
    clinical_justification: str = Field(
        ...,
        description="Clinical reasoning for the triage decision"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Chain-of-thought reasoning steps"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "2.0.0"
    protocols_loaded: int = 0
