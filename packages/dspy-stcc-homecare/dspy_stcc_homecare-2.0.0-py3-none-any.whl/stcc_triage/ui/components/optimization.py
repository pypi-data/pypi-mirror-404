"""
Optimization Component.

Displays optimization controls and status (placeholder for CLI-based optimization).
"""

import streamlit as st

from stcc_triage.nurses.roles import NurseRole, get_specialization
from stcc_triage.ui.utils import is_agent_optimized


def render_optimization():
    """
    Render the optimization tab.

    Note: Actual optimization is done via CLI due to long runtime.
    This tab provides instructions and status.
    """
    st.header("🔧 Agent Optimization")

    st.markdown(
        """
    ## About Optimization

    **Optimization** uses DSPy's BootstrapFewShot to fine-tune each nurse agent
    with domain-specific training data, improving accuracy for specialized cases.

    ### Process Overview

    1. **Load specialized training data** (e.g., wound care cases)
    2. **Run DSPy optimization** (5-10 minutes per nurse)
    3. **Save optimized agent** to `deployment/` folder
    4. **Load optimized agent** in the UI for improved performance

    ### Time & Cost

    - **Single nurse:** 5-10 minutes, ~$0.50-1.00 in API credits
    - **All nurses:** 1-2 hours, ~$5-10 in API credits

    ---
    """
    )

    # Current optimization status
    st.subheader("📊 Current Status")

    optimized_count = sum(1 for role in NurseRole if is_agent_optimized(role))
    total_count = len(NurseRole)

    st.metric(
        "Optimized Nurses",
        f"{optimized_count} / {total_count}",
        delta=f"{(optimized_count / total_count * 100):.0f}% complete",
    )

    # List of nurses and their status
    st.markdown("### Nurse Optimization Status")

    cols = st.columns(2)

    for idx, role in enumerate(NurseRole):
        spec = get_specialization(role)
        col = cols[idx % 2]

        with col:
            if is_agent_optimized(role):
                st.success(f"✅ {spec.display_name}")
            else:
                st.warning(f"⬜ {spec.display_name}")

    # Instructions
    st.divider()
    st.subheader("💻 How to Optimize")

    st.markdown("### Option 1: Optimize a Single Nurse")

    # Dropdown to select nurse
    selected_role = st.selectbox(
        "Select nurse to optimize",
        options=list(NurseRole),
        format_func=lambda r: get_specialization(r).display_name,
    )

    spec = get_specialization(selected_role)

    st.code(
        f"# Optimize {spec.display_name}\n"
        f"uv run python optimization/compile_specialized.py --role {selected_role.value}",
        language="bash",
    )

    if is_agent_optimized(selected_role):
        st.info(f"✓ {spec.display_name} is already optimized")
    else:
        st.warning(f"⚠ {spec.display_name} is not yet optimized")

    st.markdown("### Option 2: Optimize All Nurses")

    st.code(
        "# Optimize all 10 nurse specializations (1-2 hours)\n"
        "uv run python optimization/compile_specialized.py",
        language="bash",
    )

    st.markdown("### Option 3: Force Regenerate Training Data")

    st.code(
        f"# Regenerate data and optimize\n"
        f"uv run python optimization/compile_specialized.py --role {selected_role.value} --regenerate-data",
        language="bash",
    )

    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        st.markdown(
            """
        **Training Data:**
        - Location: `dataset/cases_[role]_nurse.json`
        - Size: 12-16 cases per specialization
        - Quality: Validated against STCC protocols

        **Optimization Parameters:**
        - Method: BootstrapFewShot
        - Metric: Protocol adherence + safety
        - Max bootstrapped demonstrations: 4

        **Output:**
        - Compiled agents saved to: `deployment/compiled_[role]_nurse_agent.json`
        - Load automatically when available
        """
        )

    # Refresh button
    st.divider()

    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()
