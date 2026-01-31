"""
Specialized Dataset Generator for Nurse Roles.

Generates domain-specific training cases for each nurse specialization.
"""

import json
from pathlib import Path
from typing import List

from stcc_triage.datasets.schema import PatientCase
from stcc_triage.nurses.roles import NurseRole, get_specialization
from stcc_triage.datasets.cases import (
    CHF_CASES,
    PREOP_CASES,
    ED_CASES,
    PEDIATRIC_CASES,
    WOUND_CARE_CASES,
    OB_CASES,
    NEURO_CASES,
    GI_CASES,
    MENTAL_HEALTH_CASES,
    RESPIRATORY_CASES,
)
from stcc_triage.core.paths import get_datasets_dir


def generate_specialized_dataset(
    role: NurseRole, output_dir: Path = None
) -> List[PatientCase]:
    """
    Generate domain-specific training dataset for a nurse role.

    Args:
        role: The nurse role specialization
        output_dir: Directory to save the dataset (default: user_data/datasets/)

    Returns:
        List of PatientCase objects for the specialization
    """
    specialization = get_specialization(role)

    # Select cases based on role
    if role == NurseRole.WOUND_CARE_NURSE:
        cases = WOUND_CARE_CASES
    elif role == NurseRole.OB_NURSE:
        cases = OB_CASES
    elif role == NurseRole.NEURO_NURSE:
        cases = NEURO_CASES
    elif role == NurseRole.GI_NURSE:
        cases = GI_CASES
    elif role == NurseRole.MENTAL_HEALTH_NURSE:
        cases = MENTAL_HEALTH_CASES
    elif role == NurseRole.CHF_NURSE:
        cases = CHF_CASES
    elif role == NurseRole.PREOP_NURSE:
        cases = PREOP_CASES
    elif role == NurseRole.ED_NURSE:
        cases = ED_CASES
    elif role == NurseRole.PEDIATRIC_NURSE:
        cases = PEDIATRIC_CASES
    elif role == NurseRole.RESPIRATORY_NURSE:
        cases = RESPIRATORY_CASES
    elif role == NurseRole.GENERAL_NURSE:
        # Combine all cases for general nurse
        cases = (
            WOUND_CARE_CASES
            + OB_CASES
            + NEURO_CASES
            + GI_CASES
            + MENTAL_HEALTH_CASES
            + CHF_CASES
            + PREOP_CASES
            + ED_CASES
            + PEDIATRIC_CASES
            + RESPIRATORY_CASES
        )
    else:
        # Default to general cases
        cases = WOUND_CARE_CASES + CHF_CASES + ED_CASES

    # Save to file
    if output_dir is None:
        output_dir = get_datasets_dir()

    output_file = output_dir / f"cases_{role.value}.json"
    output_dir.mkdir(exist_ok=True, parents=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(
            [case.model_dump() for case in cases],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n{specialization.display_name} Dataset Generated")
    print(f"Generated {len(cases)} specialized cases")
    print(f"Saved to: {output_file}")

    # Distribution
    distribution = {}
    for case in cases:
        distribution[case.triage_level] = distribution.get(case.triage_level, 0) + 1

    print("\nCase Distribution:")
    for level, count in sorted(distribution.items()):
        print(f"  {level}: {count} cases")

    return cases


def generate_all_specialized_datasets(output_dir: Path = None):
    """Generate datasets for all nurse specializations."""
    print("=" * 60)
    print("Specialized Nurse Dataset Generator")
    print("=" * 60)

    if output_dir is None:
        output_dir = get_datasets_dir()

    for role in [
        # Top volume categories
        NurseRole.WOUND_CARE_NURSE,
        NurseRole.OB_NURSE,
        NurseRole.PEDIATRIC_NURSE,
        # Major specialties
        NurseRole.NEURO_NURSE,
        NurseRole.GI_NURSE,
        NurseRole.RESPIRATORY_NURSE,
        NurseRole.MENTAL_HEALTH_NURSE,
        # Additional roles
        NurseRole.CHF_NURSE,
        NurseRole.ED_NURSE,
        NurseRole.PREOP_NURSE,
        NurseRole.GENERAL_NURSE,
    ]:
        generate_specialized_dataset(role, output_dir)
        print()

    print("=" * 60)
    print("All specialized datasets generated!")
    print(f"Datasets saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_specialized_datasets()
