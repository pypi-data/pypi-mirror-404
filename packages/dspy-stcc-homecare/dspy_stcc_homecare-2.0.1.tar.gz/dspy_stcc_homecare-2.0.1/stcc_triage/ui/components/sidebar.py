"""
Sidebar Component.

Handles nurse selection, loading, and optimization controls.
"""

import streamlit as st

from stcc_triage.nurses.roles import NURSE_SPECIALIZATIONS, NurseRole, get_specialization
from stcc_triage.ui.utils import is_agent_optimized, load_nurse_agent


def render_sidebar():
    """
    Render the sidebar with nurse selection and optimization.
    """
    st.header("👨‍⚕️ Nurse Selection")

    # Nurse dropdown
    selected_role = st.selectbox(
        "Select Specialization",
        options=list(NURSE_SPECIALIZATIONS.keys()),
        format_func=lambda r: NURSE_SPECIALIZATIONS[r].display_name,
        key="nurse_selector",
    )

    # Update selected role in session state
    st.session_state.selected_role = selected_role

    # Show nurse details
    spec = get_specialization(selected_role)

    st.markdown(f"**{spec.description}**")

    # Show focus areas
    if spec.focus_symptoms:
        with st.expander("Focus Areas"):
            st.markdown("**Primary Symptoms:**")
            for symptom in spec.focus_symptoms[:5]:
                st.markdown(f"- {symptom}")
            if len(spec.focus_symptoms) > 5:
                st.markdown(f"- ... and {len(spec.focus_symptoms) - 5} more")

    # Check if optimized
    st.divider()

    if is_agent_optimized(selected_role):
        st.success("✓ Optimized Agent Available")
    else:
        st.warning("⚠ Baseline Agent (Not Optimized)")

    # Load button
    if st.button("🔄 Load Nurse", use_container_width=True):
        with st.spinner(f"Loading {spec.display_name}..."):
            try:
                agent = load_nurse_agent(selected_role)
                st.session_state.loaded_nurse = agent
                st.session_state.loaded_nurse_role = selected_role

                # Clear chat history when switching nurses
                st.session_state.chat_history = []

                st.rerun()

            except Exception as e:
                st.error(f"Error loading nurse: {str(e)}")

    # Show currently loaded nurse
    if st.session_state.loaded_nurse_role:
        loaded_spec = get_specialization(st.session_state.loaded_nurse_role)
        if st.session_state.loaded_nurse_role == selected_role:
            st.info(f"✓ Currently loaded: {loaded_spec.display_name}")
        else:
            st.warning(f"Note: {loaded_spec.display_name} is loaded. Click 'Load Nurse' to switch.")

    # Optimization section
    st.divider()
    st.subheader("🔧 Optimization")

    st.markdown(
        "⏱️ **Note:** Optimization takes 5-10 minutes per nurse and requires DeepSeek API credits."
    )

    # Optimize current button
    if st.button("⚙️ Optimize Current", use_container_width=True):
        st.info(
            "Optimization is a long-running process. "
            "Please use the command line:\n\n"
            f"`stcc-optimize --role {selected_role.value}`"
        )

    # Optimize all button
    if st.button("⚙️ Optimize All Nurses", use_container_width=True):
        st.info(
            "Optimizing all nurses takes 1-2 hours. "
            "Please use the command line:\n\n"
            "`stcc-optimize`"
        )

    # Show optimization status
    with st.expander("📊 Optimization Status"):
        st.markdown("**Available Optimized Nurses:**")

        for role in NurseRole:
            role_spec = get_specialization(role)
            if is_agent_optimized(role):
                st.markdown(f"✅ {role_spec.display_name}")
            else:
                st.markdown(f"⬜ {role_spec.display_name}")
