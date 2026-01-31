"""
STCC Triage Agent with DSPy ChainOfThought.

Main triage agent using DeepSeek for medical reasoning.
"""

import json
from pathlib import Path
from typing import List

try:
    import dspy
    from dspy import ChainOfThought
except ImportError:
    raise ImportError("dspy-ai package not installed. Run: uv add dspy-ai")

from .signatures import TriageSignature, FollowUpSignature
from .settings import get_deepseek_config

# Keywords that indicate critical info is present
_INFO_KEYWORDS = {
    "duration": [
        "how long", "when", "started", "since", "days", "hours", "weeks",
        "yesterday", "today", "多久", "什么时候", "昨天", "今天",
    ],
    "severity": [
        "severe", "mild", "moderate", "unbearable", "slight",
        "严重", "轻", "重", "有点", "非常",
    ],
    "age": [
        "age", "years old", "岁", "年龄",
    ],
    "medical_history": [
        "history", "diagnosed", "disease", "diabetes", "hypertension",
        "病史", "既往", "糖尿病", "高血压", "心衰",
    ],
}

# Minimum missing categories to trigger follow-up questions
_FOLLOWUP_THRESHOLD = 3


class STCCTriageAgent:
    """
    Medical triage agent using DSPy ChainOfThought with DeepSeek.

    Features:
    - Chain-of-thought reasoning for transparent decision-making
    - STCC protocol context enhancement
    - DeepSeek-powered reasoning engine
    - Structured output with clinical justification
    """

    def __init__(self, protocols_path: str = None):
        """
        Initialize triage agent.

        Args:
            protocols_path: Path to digitized STCC protocols JSON file.
                          If None, uses default path from package data.
        """
        # Configure DeepSeek via DSPy
        config = get_deepseek_config()
        dspy.configure(lm=config.lm)

        # Load digitized protocols
        if protocols_path is None:
            # Use default path from package
            from .paths import get_protocols_json_path
            protocols_path = get_protocols_json_path()

        protocols_file = Path(protocols_path)
        if not protocols_file.exists():
            raise FileNotFoundError(
                f"Protocols file not found: {protocols_path}. "
                "Run: stcc-parse-protocols"
            )

        with open(protocols_path, "r", encoding="utf-8") as f:
            self.protocols = json.load(f)

        # Create ChainOfThought modules
        self.triage_module = ChainOfThought(TriageSignature)
        self.followup_module = ChainOfThought(FollowUpSignature)

        print(f"Triage agent initialized with {len(self.protocols)} protocols")

    def ask_or_triage(
        self,
        symptoms: str,
        conversation_history: List[str] = None,
        question_rounds: int = 0,
        max_rounds: int = 3,
    ) -> dict:
        """
        Decide whether to ask follow-up questions or perform triage.

        Asks follow-up questions if critical info is missing and we haven't
        exceeded max_rounds. Otherwise performs triage with available info.

        Args:
            symptoms: Current patient message
            conversation_history: Previous patient messages
            question_rounds: How many rounds of questions already asked
            max_rounds: Maximum follow-up rounds before forcing triage

        Returns:
            Dict with either:
                - {"action": "ask", "questions": str} for follow-up
                - {"action": "triage", "result": Prediction} for triage
        """
        full_text = symptoms
        if conversation_history:
            full_text = " ".join(conversation_history) + " " + symptoms

        missing = self._find_missing_info(full_text)

        # Ask follow-up if too much info is missing and under round limit
        if len(missing) >= _FOLLOWUP_THRESHOLD and question_rounds < max_rounds:
            prediction = self.followup_module(
                patient_message=full_text,
                missing_categories=", ".join(missing),
            )
            return {"action": "ask", "questions": prediction.follow_up_questions}

        # Otherwise triage with what we have
        result = self.triage(symptoms, conversation_history=conversation_history)
        return {"action": "triage", "result": result}

    def triage(
        self, symptoms: str, conversation_history: List[str] = None
    ) -> dspy.Prediction:
        """
        Perform triage on patient symptoms.

        Args:
            symptoms: Patient symptom description (natural language)
            conversation_history: Previous patient messages for context

        Returns:
            DSPy Prediction with:
                - triage_level: Emergency/Urgent/Moderate/Home Care
                - clinical_justification: Reasoning
                - rationale: Chain-of-thought steps (added by ChainOfThought)
        """
        # Build context from conversation history
        if conversation_history:
            context = "Patient Conversation:\n"
            for i, msg in enumerate(conversation_history, 1):
                context += f"Message {i}: {msg}\n"
            context += f"Latest message: {symptoms}"
            symptoms = context

        # Add protocol context to symptoms
        enhanced_prompt = self._add_protocol_context(symptoms)

        # Run ChainOfThought reasoning
        prediction = self.triage_module(symptoms=enhanced_prompt)

        return prediction

    def _add_protocol_context(self, symptoms: str) -> str:
        """
        Add relevant STCC protocol context to symptoms.

        CRITICAL: DSPy works best with context-rich inputs.
        Include protocol snippets matching symptom keywords.

        Args:
            symptoms: Raw patient symptom description

        Returns:
            Enhanced prompt with relevant protocol context
        """
        # Extract keywords from symptoms
        keywords = self._extract_keywords(symptoms)

        # Find matching protocols
        relevant_protocols = []
        for protocol in self.protocols:
            protocol_name_lower = protocol["protocol_name"].lower()
            if any(kw in protocol_name_lower for kw in keywords):
                relevant_protocols.append(protocol)

        # Build enhanced prompt
        context = f"Patient Presentation:\n{symptoms}\n\n"

        if relevant_protocols:
            context += "Relevant STCC Protocol Guidelines:\n"

            # Include top 2 most relevant protocols
            for protocol in relevant_protocols[:2]:
                context += f"\n{protocol['protocol_name']}:\n"

                # Add red flags (Section A - emergency)
                if protocol["sections"]:
                    emergency_section = protocol["sections"][0]
                    if emergency_section["urgency_level"] == "emergency":
                        context += "  Red Flags (Emergency - Call Ambulance):\n"
                        for condition in emergency_section["conditions"][:3]:
                            context += f"    - {condition}\n"

                # Add urgency levels and actions
                for section in protocol["sections"][:3]:  # Top 3 sections
                    level = section["urgency_level"]
                    action = section["action"]
                    context += f"  {level.title()}: {action}\n"
        else:
            # No specific protocol match - provide general guidance
            context += (
                "\nGeneral Triage Guidelines:\n"
                "- Emergency: Life-threatening symptoms requiring immediate ambulance\n"
                "- Urgent: Serious conditions needing emergency department care\n"
                "- Moderate: Needs medical evaluation within hours\n"
                "- Home Care: Can be managed with self-care at home\n"
            )

        return context

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract medical keywords for protocol matching.

        Args:
            text: Symptom description

        Returns:
            List of extracted keywords
        """
        keywords = []
        text_lower = text.lower()

        # Map common symptoms to protocol categories
        # This is simplified - in production, use medical NLP
        keyword_map = {
            "chest pain": ["chest", "pain", "cardiac", "heart"],
            "breathing": ["breathing", "respiratory", "asthma", "wheez", "dyspnea"],
            "abdominal": ["abdominal", "stomach", "belly", "abdomen"],
            "fever": ["fever", "temperature", "hot"],
            "headache": ["headache", "head pain"],
            "dizziness": ["dizzy", "lightheaded", "vertigo"],
            "nausea": ["nausea", "vomit", "nauseated"],
        }

        for category, terms in keyword_map.items():
            if any(term in text_lower for term in terms):
                keywords.append(category)

        return keywords if keywords else ["general"]

    @staticmethod
    def _find_missing_info(text: str) -> List[str]:
        """
        Check which critical info categories are missing from text.

        Args:
            text: Combined patient messages

        Returns:
            List of missing category names
        """
        text_lower = text.lower()
        missing = []
        for category, keywords in _INFO_KEYWORDS.items():
            if not any(kw in text_lower for kw in keywords):
                missing.append(category)
        return missing


if __name__ == "__main__":
    # Test agent initialization
    try:
        agent = STCCTriageAgent()
        print("Agent initialized successfully!")

        # Test triage (requires DeepSeek API key in .env)
        test_symptoms = "55-year-old male with severe chest pain and shortness of breath"
        print(f"\nTest symptoms: {test_symptoms}")

        result = agent.triage(test_symptoms)
        print(f"Triage Level: {result.triage_level}")
        print(f"Justification: {result.clinical_justification}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Run: stcc-parse-protocols")
        print("2. Create .env file with DEEPSEEK_API_KEY")
