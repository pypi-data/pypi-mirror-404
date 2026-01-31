"""
Triage Result Card Component.

Displays triage results with color-coded severity levels.
"""

import streamlit as st

from stcc_triage.ui.utils import format_triage_level, get_level_color, get_level_emoji


def render_triage_card(result):
    """
    Render a triage result card.

    Args:
        result: DSPy Prediction object with triage_level, clinical_justification, rationale
    """
    # Extract triage level
    triage_level = result.triage_level
    emoji = get_level_emoji(triage_level)
    color = get_level_color(triage_level)
    formatted_level = format_triage_level(triage_level)

    # Display card with color border
    st.markdown(
        f"""
        <div style="
            border: 3px solid {color};
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            background-color: {color}10;
        ">
            <h2 style="color: {color}; margin: 0;">
                {emoji} {formatted_level}
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display clinical justification
    st.markdown("**Clinical Justification:**")
    st.write(result.clinical_justification)

    # Display reasoning steps in expander
    if hasattr(result, "rationale") and result.rationale:
        with st.expander("🔍 View Reasoning Steps"):
            st.write(result.rationale)
