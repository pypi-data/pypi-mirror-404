"""
DSPy Signature for Medical Triage.

Defines the input/output structure for the triage agent.
"""

try:
    import dspy
except ImportError:
    raise ImportError(
        "dspy-ai package not installed. Run: uv add dspy-ai"
    )


class FollowUpSignature(dspy.Signature):
    """
    Generate natural follow-up questions when patient information is incomplete.

    Acts as an experienced triage nurse. Respond in the SAME LANGUAGE as the patient.
    """

    patient_message = dspy.InputField(
        desc=(
            "The patient's message(s) so far. May be in any language."
        )
    )

    missing_categories = dspy.InputField(
        desc=(
            "Comma-separated list of missing critical information, "
            "e.g.: duration, severity, age, medical history, medications, "
            "associated symptoms."
        )
    )

    follow_up_questions = dspy.OutputField(
        desc=(
            "Natural, empathetic follow-up questions in the SAME LANGUAGE "
            "as the patient. Be conversational like a real nurse. "
            "Ask 2-4 focused questions. Do NOT provide any triage or diagnosis."
        )
    )


class TriageSignature(dspy.Signature):
    """
    Medical triage signature following STCC protocols.

    Maps patient symptoms to triage level with clinical reasoning.
    Uses DSPy's declarative signature format for clear input/output specification.
    """

    # Input: Patient presentation
    symptoms = dspy.InputField(
        desc=(
            "Patient symptoms description including: "
            "chief complaint, duration, severity, associated symptoms, "
            "age, relevant medical history, current medications. "
            "May include relevant STCC protocol context."
        )
    )

    # Output: Triage decision
    triage_level = dspy.OutputField(
        desc=(
            "Triage urgency level based on STCC protocols. "
            "Must be exactly one of: Emergency, Urgent, Moderate, Home Care. "
            "Emergency = life-threatening (call ambulance). "
            "Urgent = needs immediate medical attention (ED within hours). "
            "Moderate = needs medical evaluation (within 2-4 hours). "
            "Home Care = can be managed at home with self-care."
        )
    )

    clinical_justification = dspy.OutputField(
        desc=(
            "Clinical reasoning for this triage decision. "
            "Reference specific STCC protocol criteria that were matched. "
            "Note any red-flag symptoms detected (chest pain, breathing difficulty, etc.). "
            "Explain why this urgency level was chosen over others."
        )
    )
