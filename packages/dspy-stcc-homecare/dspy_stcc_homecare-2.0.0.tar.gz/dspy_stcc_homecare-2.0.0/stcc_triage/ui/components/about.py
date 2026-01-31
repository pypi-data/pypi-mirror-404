"""
About/Help Component.

Displays project information, usage instructions, and disclaimers.
"""

import streamlit as st


def render_about():
    """
    Render the about/help tab.
    """
    st.header("About STCC Triage Agent")

    st.markdown(
        """
    ## Overview

    The **STCC Triage Agent** is an AI-powered medical triage system with
    **10 specialized "remote nurses"**, each expert in their clinical domain.

    ### Available Nurse Specializations

    | Nurse | Specialization | Coverage |
    |-------|---------------|----------|
    | **Wound Care** | Trauma, burns, bleeding | 24 protocols |
    | **OB/Maternal** | Pregnancy, labor, postpartum | 13 protocols |
    | **Pediatric** | Children & infants | 12 protocols |
    | **Neuro** | Stroke, seizure, neurological | 7 protocols |
    | **GI** | Abdominal, digestive | 6 protocols |
    | **Respiratory** | Breathing, asthma, COPD | 6 protocols |
    | **Mental Health** | Behavioral crises | 5 protocols |
    | **CHF** | Heart failure, cardiac | 4 protocols |
    | **ED** | Emergency/acute care | All protocols |
    | **PreOp** | Pre-surgical assessment | 2 protocols |

    ### How It Works

    1. **Select a specialized nurse** from the sidebar based on your symptoms
    2. **Load the nurse** to activate the agent
    3. **Describe your symptoms** in the chat interface
    4. **Receive a triage recommendation** with clinical justification

    ### Triage Levels

    - 🚨 **Emergency**: Life-threatening - Call ambulance immediately
    - ⚠️ **Urgent**: Serious condition - Go to emergency department
    - ⚡ **Moderate**: Needs medical evaluation within hours
    - ✅ **Home Care**: Can be managed with self-care at home

    ### Optimization

    **Baseline vs Optimized Agents:**
    - **Baseline**: Uses general medical knowledge
    - **Optimized**: Fine-tuned with domain-specific training data using DSPy

    **To optimize a nurse:**
    ```bash
    python optimization/compile_specialized.py --role wound_care_nurse
    ```

    ### Technology Stack

    - **DSPy**: Prompt optimization framework
    - **DeepSeek**: Medical reasoning engine
    - **Streamlit**: Interactive UI
    - **STCC Protocols**: 225 digitized clinical protocols

    ## ⚠️ Important Disclaimers

    ### Educational Use Only

    This system is designed for:
    - Educational purposes
    - Research and development
    - Demonstration of AI capabilities

    ### NOT for Clinical Use

    - ❌ NOT FDA approved
    - ❌ NOT a substitute for professional medical advice
    - ❌ NOT for use in actual medical emergencies
    - ❌ NOT validated for real-world deployment

    ### Always Consult Healthcare Professionals

    If you have a medical emergency:
    - 🚨 Call 911 (US) or your local emergency number
    - 🏥 Go to the nearest emergency department
    - 📞 Contact your healthcare provider

    ## Support

    For issues or questions about this system:
    - Check the README.md file
    - Review the example cases
    - Contact the development team

    ## License

    MIT License - Educational and research use only.
    """
    )
