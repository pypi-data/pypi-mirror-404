"""
CLI command for optimizing specialized nurses.

Entry point for stcc-optimize command.
"""

import argparse
from stcc_triage.nurses.roles import NurseRole
from stcc_triage.optimizers.compiler import optimize_nurse


def main():
    """Optimize specialized nurse agents."""
    parser = argparse.ArgumentParser(
        description="Optimize specialized nurse agents with BootstrapFewShot"
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=[r.value for r in NurseRole],
        help="Specific role to compile (default: all roles)",
    )
    parser.add_argument(
        "--regenerate-data",
        action="store_true",
        help="Force regenerate training data before optimization",
    )

    args = parser.parse_args()

    # Run optimization
    optimize_nurse(role=args.role, regenerate_data=args.regenerate_data)


if __name__ == "__main__":
    main()
