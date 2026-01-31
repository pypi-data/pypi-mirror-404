"""
Compile Specialized Nurse Agents.

Optimizes triage agents for specific nurse roles using domain-targeted training data.
"""

import dspy
import json
from pathlib import Path
from typing import Optional

from stcc_triage.core.agent import STCCTriageAgent
from stcc_triage.core.settings import get_deepseek_config
from stcc_triage.core.paths import get_compiled_dir, get_datasets_dir
from stcc_triage.nurses.roles import NurseRole, get_specialization
from stcc_triage.datasets.generator import generate_specialized_dataset
from stcc_triage.datasets.schema import PatientCase
from stcc_triage.optimizers.optimizer import get_optimizer


def compile_specialized_agent(
    role: NurseRole,
    force_regenerate_data: bool = False,
    output_dir: Optional[Path] = None,
) -> str:
    """
    Compile a specialized triage agent for a specific nurse role.

    Args:
        role: The nurse role specialization
        force_regenerate_data: Whether to regenerate training data
        output_dir: Directory to save compiled agent (default: user_data/compiled/)

    Returns:
        Path to the compiled agent JSON file
    """
    specialization = get_specialization(role)

    print("=" * 70)
    print(f"Compiling Specialized Agent: {specialization.display_name}")
    print("=" * 70)
    print(f"Description: {specialization.description}")
    print(f"Focus areas: {', '.join(specialization.focus_symptoms[:5])}...")
    print()

    # Step 1: Load or generate specialized training data
    datasets_dir = get_datasets_dir()
    dataset_path = datasets_dir / f"cases_{role.value}.json"

    if not dataset_path.exists() or force_regenerate_data:
        print("Generating specialized training dataset...")
        generate_specialized_dataset(role)
    else:
        print(f"Using existing dataset: {dataset_path}")

    # Load training cases
    with dataset_path.open("r", encoding="utf-8") as f:
        cases_data = json.load(f)

    patient_cases = [PatientCase(**case) for case in cases_data]

    print(f"\nTraining set: {len(patient_cases)} specialized cases")
    distribution = {}
    for case in patient_cases:
        distribution[case.triage_level] = distribution.get(case.triage_level, 0) + 1

    print("Distribution:")
    for level, count in sorted(distribution.items()):
        print(f"  {level}: {count} cases")

    # Convert to DSPy Example format
    trainset = []
    for case in patient_cases:
        example = dspy.Example(
            symptoms=case.symptoms,
            triage_level=case.triage_level,
        ).with_inputs("symptoms")
        example.case = case
        trainset.append(example)

    # Step 2: Initialize agent
    print("\nInitializing triage agent...")
    config = get_deepseek_config()
    dspy.configure(lm=config.lm)

    agent = STCCTriageAgent()

    # Step 3: Optimize with BootstrapFewShot
    print(f"\nOptimizing for {specialization.display_name}...")
    print("This may take 5-10 minutes...")

    teleprompter = get_optimizer()

    # Compile with domain-specific training data
    compiled_agent = teleprompter.compile(
        student=agent.triage_module,
        trainset=trainset,
    )

    # Step 4: Save compiled agent
    if output_dir is None:
        output_dir = get_compiled_dir()

    output_path = output_dir / f"compiled_{role.value}_agent.json"
    output_path.parent.mkdir(exist_ok=True, parents=True)

    compiled_agent.save(str(output_path))

    print(f"\n✓ Compiled {specialization.display_name} agent saved to:")
    print(f"  {output_path}")

    return str(output_path)


def compile_all_specializations(output_dir: Optional[Path] = None):
    """
    Compile agents for all nurse specializations.

    Args:
        output_dir: Directory to save compiled agents (default: user_data/compiled/)
    """
    print("\n" + "=" * 70)
    print("SPECIALIZED NURSE AGENT COMPILER")
    print("=" * 70)

    roles = [
        # Top volume categories (cover most protocols)
        NurseRole.WOUND_CARE_NURSE,  # 24 protocols
        NurseRole.OB_NURSE,          # 13 protocols
        NurseRole.PEDIATRIC_NURSE,   # 12 protocols
        # Major specialties
        NurseRole.NEURO_NURSE,       # 7 protocols
        NurseRole.GI_NURSE,          # 6 protocols
        NurseRole.RESPIRATORY_NURSE, # 6 protocols
        NurseRole.MENTAL_HEALTH_NURSE, # 5 protocols
        # Additional specialties
        NurseRole.CHF_NURSE,         # 4 protocols
        NurseRole.ED_NURSE,
        NurseRole.PREOP_NURSE,       # 2 protocols
    ]

    compiled_agents = {}

    for role in roles:
        try:
            output_path = compile_specialized_agent(
                role,
                force_regenerate_data=False,
                output_dir=output_dir
            )
            compiled_agents[role.value] = output_path
            print()
        except Exception as e:
            print(f"\n✗ Error compiling {role.value}: {e}")
            print()

    # Summary
    print("=" * 70)
    print("COMPILATION SUMMARY")
    print("=" * 70)

    for role_name, path in compiled_agents.items():
        spec = get_specialization(NurseRole(role_name))
        print(f"✓ {spec.display_name:20s} → {Path(path).name}")

    print(f"\nTotal: {len(compiled_agents)} specialized agents compiled")
    print("=" * 70)


def load_compiled_nurse(role: NurseRole, compiled_dir: Optional[Path] = None) -> dspy.Module:
    """
    Load a compiled nurse agent from disk.

    Args:
        role: The nurse role to load
        compiled_dir: Directory containing compiled agents (default: user_data/compiled/)

    Returns:
        Compiled DSPy module

    Raises:
        FileNotFoundError: If compiled agent not found
    """
    if compiled_dir is None:
        compiled_dir = get_compiled_dir()

    compiled_path = compiled_dir / f"compiled_{role.value}_agent.json"

    if not compiled_path.exists():
        raise FileNotFoundError(
            f"Compiled agent not found: {compiled_path}\n"
            f"Run: stcc-optimize --role {role.value}"
        )

    # Load the compiled module
    # Note: DSPy's load mechanism may vary by version
    # This is a placeholder - actual implementation depends on DSPy API
    import dspy
    from stcc_triage.core.signatures import TriageSignature
    from dspy import ChainOfThought

    module = ChainOfThought(TriageSignature)
    module.load(str(compiled_path))

    return module


# Convenience function for CLI
def optimize_nurse(role: Optional[str] = None, regenerate_data: bool = False):
    """
    CLI-friendly optimization function.

    Args:
        role: Nurse role name (e.g., 'wound_care_nurse') or None for all
        regenerate_data: Whether to regenerate training data
    """
    if role:
        # Compile single role
        compile_specialized_agent(
            NurseRole(role),
            force_regenerate_data=regenerate_data,
        )
    else:
        # Compile all roles
        compile_all_specializations()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compile specialized nurse agents")
    parser.add_argument(
        "--role",
        type=str,
        choices=[r.value for r in NurseRole],
        help="Specific role to compile (default: all)",
    )
    parser.add_argument(
        "--regenerate-data",
        action="store_true",
        help="Force regenerate training data",
    )

    args = parser.parse_args()

    optimize_nurse(role=args.role, regenerate_data=args.regenerate_data)
