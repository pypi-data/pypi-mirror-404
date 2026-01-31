"""
Specialized Nurse Demo.

Demonstrates using different specialized nurse agents for domain-specific triage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.triage_agent import STCCTriageAgent
from dataset.nurse_roles import NurseRole, get_specialization


def demo_specialized_nurse(role: NurseRole, symptoms: str):
    """
    Demo a specialized nurse performing triage.

    Args:
        role: The nurse specialization
        symptoms: Patient symptoms
    """
    spec = get_specialization(role)

    print(f"\n{'='*70}")
    print(f"👨‍⚕️  {spec.display_name}")
    print(f"{'='*70}")
    print(f"Specialty: {spec.description}")
    print(f"\nPatient Symptoms:")
    print(f"  {symptoms}")

    # Load specialized agent
    agent = STCCTriageAgent()

    compiled_path = Path(__file__).parent.parent / "deployment" / f"compiled_{role.value}_agent.json"

    if compiled_path.exists():
        print(f"\n✓ Using optimized {spec.display_name} agent")
        agent.triage_module.load(str(compiled_path))
    else:
        print(f"\n⚠ Using baseline agent (optimize with: python optimization/compile_specialized.py --role {role.value})")

    # Perform triage
    try:
        result = agent.triage(symptoms)

        print(f"\n{'─'*70}")
        print(f"TRIAGE RESULT")
        print(f"{'─'*70}")
        print(f"Level: {result.triage_level.upper()}")
        print(f"\nClinical Justification:")
        print(f"  {result.clinical_justification}")
        print(f"{'─'*70}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Run specialized nurse demonstrations."""
    print("\n" + "=" * 70)
    print("SPECIALIZED NURSE TRIAGE DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how different nurse specializations handle")
    print("domain-specific patient cases.\n")

    # CHF Nurse Example
    demo_specialized_nurse(
        role=NurseRole.CHF_NURSE,
        symptoms=(
            "68-year-old with known CHF, weight gain 5kg in 2 days, "
            "increasing dyspnea on exertion, ankle swelling worsening, "
            "using 3 pillows to sleep at night"
        ),
    )

    # PreOp Nurse Example
    demo_specialized_nurse(
        role=NurseRole.PREOP_NURSE,
        symptoms=(
            "58-year-old scheduled for hip surgery in 3 days, "
            "blood pressure 180/110 at home, has been taking aspirin daily, "
            "history of hypertension but hasn't seen doctor in 6 months"
        ),
    )

    # ED Nurse Example
    demo_specialized_nurse(
        role=NurseRole.ED_NURSE,
        symptoms=(
            "35-year-old motor vehicle accident victim, awake but confused, "
            "complaining of severe head and neck pain, visible lacerations, "
            "blood pressure 90/60"
        ),
    )

    # Pediatric Nurse Example
    demo_specialized_nurse(
        role=NurseRole.PEDIATRIC_NURSE,
        symptoms=(
            "18-month-old with fever 39.5°C for 2 days, vomiting, "
            "decreased wet diapers (only 1 in past 8 hours), "
            "lethargic, dry lips"
        ),
    )

    # Respiratory Nurse Example
    demo_specialized_nurse(
        role=NurseRole.RESPIRATORY_NURSE,
        symptoms=(
            "58-year-old COPD patient with increased shortness of breath, "
            "unable to speak full sentences, using accessory muscles, "
            "productive cough with yellow-green sputum, O2 sat 85%"
        ),
    )

    print("\n" + "=" * 70)
    print("COMPARISON: General vs Specialized Nurse")
    print("=" * 70)
    print("\nSame cardiac case evaluated by different nurses:")

    cardiac_symptoms = (
        "72-year-old with chest pain, severe dyspnea, cold extremities, "
        "history of CHF"
    )

    print(f"\n📋 Patient: {cardiac_symptoms}")

    # General nurse
    print("\n1️⃣  GENERAL NURSE (Broad training)")
    agent_general = STCCTriageAgent()
    result_general = agent_general.triage(cardiac_symptoms)
    print(f"   Triage: {result_general.triage_level}")
    print(f"   Reasoning: {result_general.clinical_justification[:150]}...")

    # CHF specialist (if available)
    print("\n2️⃣  CHF NURSE (Specialized training)")
    agent_chf = STCCTriageAgent()
    chf_compiled = Path(__file__).parent.parent / "deployment" / "compiled_chf_nurse_agent.json"

    if chf_compiled.exists():
        agent_chf.triage_module.load(str(chf_compiled))
        result_chf = agent_chf.triage(cardiac_symptoms)
        print(f"   Triage: {result_chf.triage_level}")
        print(f"   Reasoning: {result_chf.clinical_justification[:150]}...")
    else:
        print("   ⚠ Not optimized yet - run: python optimization/compile_specialized.py --role chf_nurse")

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Specialized nurses focus on domain-specific cases")
    print("  • Training data is targeted to each specialty")
    print("  • More accurate few-shot examples = better triage")
    print("  • Version control different compiled agents")
    print("  • Load appropriate nurse based on patient symptoms")
    print()


if __name__ == "__main__":
    main()
