"""
Session State Management for Streamlit UI.

Manages nurse selection, chat history, and optimization processes.
"""

import streamlit as st

from stcc_triage.nurses.roles import NurseRole


def init_session_state():
    """
    Initialize Streamlit session state.

    Creates session state variables for:
    - Nurse management (loaded nurse, selected role)
    - Chat history
    - Optimization tracking
    """
    if "initialized" not in st.session_state:
        # Nurse management
        st.session_state.loaded_nurse = None
        st.session_state.loaded_nurse_role = None
        st.session_state.selected_role = NurseRole.WOUND_CARE_NURSE

        # Chat history
        st.session_state.chat_history = []

        # Optimization tracking
        st.session_state.optimization_processes = {}

        # Mark as initialized
        st.session_state.initialized = True
