"""
Basic Triage Example.

Demonstrates simple usage of the STCC triage agent.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.triage_agent import STCCTriageAgent


def main():
    """Run basic triage examples."""

    print("=" * 60)
    print("STCC Triage Agent - Basic Usage Example")
    print("=" * 60)

    # Initialize agent
    print("\nInitializing agent...")
    agent = STCCTriageAgent()

    # Load compiled version if available
    compiled_path = Path("deployment/compiled_triage_agent.json")
    if compiled_path.exists():
        print(f"Loading optimized agent from {compiled_path}")
        agent.triage_module.load(str(compiled_path))
    else:
        print("Using base agent (run optimization/compile_specialized.py to optimize)")

    # Test cases
    test_cases = [
        {
            "name": "Emergency - Chest Pain",
            "symptoms": "65-year-old male with severe crushing chest pain radiating to left arm, shortness of breath, cold sweaty skin",
        },
        {
            "name": "Urgent - Abdominal Pain",
            "symptoms": "45-year-old female with severe right lower abdominal pain for 6 hours, fever 38.5°C, nausea",
        },
        {
            "name": "Moderate - Respiratory Infection",
            "symptoms": "30-year-old with cough and fever 37.8°C for 2 days, mild shortness of breath",
        },
        {
            "name": "Home Care - Mild Headache",
            "symptoms": "25-year-old with mild headache after long day at computer, no other symptoms",
        },
    ]

    # Run triage on each case
    print("\n" + "=" * 60)
    print("Triage Results")
    print("=" * 60)

    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 60)
        print(f"Symptoms: {case['symptoms']}")

        try:
            result = agent.triage(case["symptoms"])

            print(f"\nTriage Level: {result.triage_level}")
            print(f"Clinical Justification:\n  {result.clinical_justification}")

        except Exception as e:
            print(f"\nError: {e}")

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
