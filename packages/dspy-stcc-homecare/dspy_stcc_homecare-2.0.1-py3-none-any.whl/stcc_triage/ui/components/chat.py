"""
Chat Interface Component.

Handles patient symptom input and triage display.
"""

import streamlit as st

from stcc_triage.ui.components.triage_card import render_triage_card


def render_chat():
    """
    Render the chat interface.

    Displays chat history and handles user input for triage.
    """
    # Display disclaimer
    st.warning("⚠️ Educational use only - NOT for clinical decisions")
    st.info("ℹ️ Always consult a qualified healthcare professional")

    # Check if nurse is loaded
    if st.session_state.loaded_nurse is None:
        st.warning("👈 Please load a nurse from the sidebar to begin")
        return

    # Display loaded nurse info
    if st.session_state.loaded_nurse_role:
        from stcc_triage.nurses.roles import get_specialization

        spec = get_specialization(st.session_state.loaded_nurse_role)
        st.success(f"**Active Nurse:** {spec.display_name}")

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "nurse":
            with st.chat_message("assistant", avatar="🤖"):
                if "triage_result" in msg:
                    render_triage_card(msg["triage_result"])
                else:
                    st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])

    # Track follow-up question rounds
    if "question_rounds" not in st.session_state:
        st.session_state.question_rounds = 0

    # Input area
    user_input = st.chat_input("Describe your symptoms...")

    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "patient", "content": user_input})

        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Build conversation history
        conversation_history = [
            msg["content"]
            for msg in st.session_state.chat_history
            if msg["role"] == "patient"
        ]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing symptoms..."):
                try:
                    response = st.session_state.loaded_nurse.ask_or_triage(
                        user_input,
                        conversation_history=conversation_history,
                        question_rounds=st.session_state.question_rounds,
                        max_rounds=3,
                    )

                    if response["action"] == "ask":
                        # Show follow-up questions
                        st.markdown(response["questions"])
                        st.session_state.chat_history.append(
                            {"role": "nurse", "content": response["questions"]}
                        )
                        st.session_state.question_rounds += 1
                    else:
                        # Show triage result
                        result = response["result"]
                        st.session_state.chat_history.append(
                            {"role": "nurse", "triage_result": result}
                        )
                        render_triage_card(result)
                        # Reset rounds after triage
                        st.session_state.question_rounds = 0

                except Exception as e:
                    error_msg = f"Error during triage: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append(
                        {"role": "nurse", "content": error_msg}
                    )


def render_chat_controls():
    """
    Render chat control buttons.
    """
    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.question_rounds = 0
            st.rerun()
