"""
FastAPI Application for STCC Triage Agent.

RESTful API for medical triage with specialized nurses.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from stcc_triage.core.agent import STCCTriageAgent
from stcc_triage.nurses.roles import NurseRole
from stcc_triage.api.models import TriageRequest, TriageResponse, HealthResponse

# Create FastAPI app
app = FastAPI(
    title="STCC Triage Agent API",
    description="Medical triage API using DSPy and DeepSeek",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize triage agent (lazy loading)
_agent = None


def get_agent() -> STCCTriageAgent:
    """Get or initialize the triage agent."""
    global _agent
    if _agent is None:
        _agent = STCCTriageAgent()
    return _agent


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    agent = get_agent()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        protocols_loaded=len(agent.protocols)
    )


@app.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest):
    """
    Perform medical triage on patient symptoms.

    Args:
        request: TriageRequest with symptoms and optional context

    Returns:
        TriageResponse with triage level and clinical justification
    """
    try:
        agent = get_agent()

        # Perform triage
        result = agent.triage(
            symptoms=request.symptoms,
            conversation_history=request.conversation_history
        )

        # Convert DSPy Prediction to response model
        return TriageResponse(
            triage_level=result.triage_level,
            clinical_justification=result.clinical_justification,
            rationale=getattr(result, 'rationale', None)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/triage/specialized", response_model=TriageResponse)
async def triage_specialized(request: TriageRequest):
    """
    Perform triage with a specialized nurse.

    Args:
        request: TriageRequest with nurse_role specified

    Returns:
        TriageResponse with specialized triage decision
    """
    if not request.nurse_role:
        raise HTTPException(
            status_code=400,
            detail="nurse_role is required for specialized triage"
        )

    try:
        # Load specialized nurse
        from stcc_triage.optimizers.compiler import load_compiled_nurse

        role = NurseRole(request.nurse_role)
        compiled_module = load_compiled_nurse(role)

        # Create agent with compiled module
        agent = get_agent()
        agent.triage_module = compiled_module

        # Perform triage
        result = agent.triage(
            symptoms=request.symptoms,
            conversation_history=request.conversation_history
        )

        return TriageResponse(
            triage_level=result.triage_level,
            clinical_justification=result.clinical_justification,
            rationale=getattr(result, 'rationale', None)
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Compiled nurse not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
