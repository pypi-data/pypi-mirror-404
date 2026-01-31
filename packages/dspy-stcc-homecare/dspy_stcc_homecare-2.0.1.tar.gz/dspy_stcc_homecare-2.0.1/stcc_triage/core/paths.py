"""
Path management utilities for STCC Triage package.

Centralizes all path handling for package data and user-generated files.
"""

from pathlib import Path
import os


def get_package_root():
    """Get package root directory."""
    return Path(__file__).parent.parent


def get_protocols_dir():
    """
    Get protocols directory from package data.

    Returns:
        Path to STCC-chinese protocols directory
    """
    # For local installation, protocols are in the package data
    protocols_dir = get_package_root() / "data" / "protocols" / "STCC-chinese"

    if not protocols_dir.exists():
        raise FileNotFoundError(
            f"Protocols directory not found: {protocols_dir}\n"
            "The STCC-chinese protocols should be included with the package."
        )

    return protocols_dir


def get_protocols_json_path():
    """
    Get path to protocols.json file.

    Returns:
        Path to protocols.json in package data, repo root, or user data directory
    """
    # Check bundled package data first (for pip-installed package)
    bundled_protocols = get_package_root() / "data" / "protocols.json"
    if bundled_protocols.exists():
        return bundled_protocols

    # Check repo root second (for development)
    repo_root = get_package_root().parent
    protocols_json = repo_root / "protocols" / "protocols.json"

    if protocols_json.exists():
        return protocols_json

    # Fallback to user data directory
    user_data_protocols = get_user_data_dir() / "protocols.json"

    if not user_data_protocols.exists():
        raise FileNotFoundError(
            f"protocols.json not found. Run: stcc-parse-protocols\n"
            f"Checked locations:\n"
            f"  - {bundled_protocols}\n"
            f"  - {protocols_json}\n"
            f"  - {user_data_protocols}"
        )

    return user_data_protocols


def get_user_data_dir():
    """
    Get user data directory for compiled agents and generated data.

    Returns:
        Path to user_data directory
    """
    # Check repo first (for development), then home directory
    repo_user_data = get_package_root().parent / "user_data"

    if repo_user_data.parent.exists():  # Check if we're in repo
        repo_user_data.mkdir(parents=True, exist_ok=True)
        return repo_user_data

    # Fallback to home directory
    default = Path.home() / ".stcc_triage"
    user_data = Path(os.getenv("STCC_DATA_DIR", default))
    user_data.mkdir(parents=True, exist_ok=True)

    return user_data


def get_compiled_dir():
    """
    Get directory for compiled nurse agents.

    Returns:
        Path to compiled agents directory
    """
    compiled_dir = get_user_data_dir() / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    return compiled_dir


def get_datasets_dir():
    """
    Get directory for generated datasets.

    Returns:
        Path to datasets directory
    """
    datasets_dir = get_user_data_dir() / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    return datasets_dir
