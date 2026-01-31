"""
STCC Triage Agent Streamlit UI.

Interactive interface for specialized nurse triage agents.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st  # noqa: E402

from stcc_triage.ui.components.about import render_about  # noqa: E402
from stcc_triage.ui.components.chat import render_chat, render_chat_controls  # noqa: E402
from stcc_triage.ui.components.optimization import render_optimization  # noqa: E402
from stcc_triage.ui.components.sidebar import render_sidebar  # noqa: E402
from stcc_triage.ui.state import init_session_state  # noqa: E402
from stcc_triage.ui.utils import check_prerequisites  # noqa: E402

# Page configuration
st.set_page_config(
    page_title="STCC Triage Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Main header
st.title("🏥 STCC Triage Agent")
st.markdown("**AI-Powered Medical Triage with Specialized Nurse Agents**")

# Check prerequisites
if not check_prerequisites():
    st.stop()

# Sidebar
with st.sidebar:
    render_sidebar()

# Main content tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "🔧 Optimization", "ℹ️ About"])

with tab1:
    render_chat_controls()
    render_chat()

with tab2:
    render_optimization()

with tab3:
    render_about()

# Footer
st.divider()
st.markdown(
    """
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>⚠️ Educational use only - NOT for clinical decisions | Always consult a healthcare professional</p>
    <p>Powered by DSPy + DeepSeek | Built with Streamlit</p>
</div>
""",
    unsafe_allow_html=True,
)
