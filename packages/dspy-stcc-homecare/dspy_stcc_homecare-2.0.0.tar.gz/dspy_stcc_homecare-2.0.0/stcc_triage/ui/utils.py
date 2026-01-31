"""
Utility Functions for Streamlit UI.

Helper functions for nurse loading, path handling, and error management.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dspy  # noqa: E402

from stcc_triage.core.settings import get_deepseek_config  # noqa: E402
from stcc_triage.core.agent import STCCTriageAgent  # noqa: E402
from stcc_triage.core.paths import get_protocols_json_path  # noqa: E402
from stcc_triage.nurses.roles import NurseRole, get_specialization  # noqa: E402


def check_prerequisites() -> bool:
    """
    Check if all prerequisites are met.

    Returns:
        True if all prerequisites are met, False otherwise
    """
    # Check API key
    try:
        get_deepseek_config()  # Just check if config exists
    except Exception:
        st.error("⚠️ DeepSeek API key not configured")
        st.code("Add to .env: DEEPSEEK_API_KEY=your_key")
        return False

    # Check protocols
    try:
        protocols_path = get_protocols_json_path()
    except FileNotFoundError:
        st.error("⚠️ Protocols not found")
        st.code("Run: python protocols/parser.py")
        return False

    return True


def get_compiled_agent_path(role: NurseRole) -> Path:
    """
    Get path to compiled agent JSON file.

    Args:
        role: The nurse role

    Returns:
        Path to compiled agent file
    """
    return project_root / "deployment" / f"compiled_{role.value}_agent.json"


def is_agent_optimized(role: NurseRole) -> bool:
    """
    Check if an agent has been optimized.

    Args:
        role: The nurse role

    Returns:
        True if optimized agent exists, False otherwise
    """
    return get_compiled_agent_path(role).exists()


def load_nurse_agent(role: NurseRole) -> STCCTriageAgent:
    """
    Load a nurse agent (optimized or baseline).

    Args:
        role: The nurse role to load

    Returns:
        Loaded STCCTriageAgent instance

    Raises:
        Exception: If agent cannot be loaded
    """
    spec = get_specialization(role)

    # Configure DSPy
    config = get_deepseek_config()
    dspy.configure(lm=config.lm)

    # Initialize base agent
    agent = STCCTriageAgent()

    # Load optimized version if available
    compiled_path = get_compiled_agent_path(role)
    if compiled_path.exists():
        agent.triage_module.load(str(compiled_path))
        st.success(f"✓ Loaded optimized {spec.display_name}")
    else:
        st.info(f"Loaded baseline {spec.display_name} (not optimized)")

    return agent


def format_triage_level(level: str) -> str:
    """
    Format triage level string for display.

    Args:
        level: Triage level string

    Returns:
        Formatted level string
    """
    return level.replace("_", " ").title()


def get_level_color(level: str) -> str:
    """
    Get color code for triage level.

    Args:
        level: Triage level

    Returns:
        Hex color code
    """
    level_lower = level.lower().replace(" ", "_")

    colors = {
        "emergency": "#dc3545",
        "urgent": "#fd7e14",
        "moderate": "#ffc107",
        "home_care": "#28a745",
    }

    return colors.get(level_lower, "#6c757d")


def get_level_emoji(level: str) -> str:
    """
    Get emoji for triage level.

    Args:
        level: Triage level

    Returns:
        Emoji string
    """
    level_lower = level.lower().replace(" ", "_")

    emojis = {
        "emergency": "🚨",
        "urgent": "⚠️",
        "moderate": "⚡",
        "home_care": "✅",
    }

    return emojis.get(level_lower, "ℹ️")
