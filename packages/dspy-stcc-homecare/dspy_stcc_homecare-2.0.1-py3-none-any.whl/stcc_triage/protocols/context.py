"""
Protocol Context Enrichment.

Functions for adding STCC protocol context to patient symptoms.
"""

from typing import List
import json
from pathlib import Path


def load_protocols(protocols_path: str = None) -> List[dict]:
    """
    Load parsed STCC protocols from JSON file.

    Args:
        protocols_path: Path to protocols.json (default: auto-detect from package)

    Returns:
        List of protocol dictionaries
    """
    if protocols_path is None:
        from stcc_triage.core.paths import get_protocols_json_path
        protocols_path = get_protocols_json_path()

    with open(protocols_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_keywords(text: str) -> List[str]:
    """
    Extract medical keywords from symptom text.

    Args:
        text: Symptom description

    Returns:
        List of extracted keywords for protocol matching
    """
    keywords = []
    text_lower = text.lower()

    # Map common symptoms to protocol categories
    keyword_map = {
        "chest pain": ["chest", "pain", "cardiac", "heart"],
        "breathing": ["breathing", "respiratory", "asthma", "wheez", "dyspnea"],
        "abdominal": ["abdominal", "stomach", "belly", "abdomen"],
        "fever": ["fever", "temperature", "hot"],
        "headache": ["headache", "head pain"],
        "dizziness": ["dizzy", "lightheaded", "vertigo"],
        "nausea": ["nausea", "vomit", "nauseated"],
        "wound": ["laceration", "cut", "wound", "bleeding", "burn"],
        "pregnancy": ["pregnancy", "pregnant", "labor", "contractions"],
    }

    for category, terms in keyword_map.items():
        if any(term in text_lower for term in terms):
            keywords.append(category)

    return keywords if keywords else ["general"]


def add_protocol_context(symptoms: str, protocols: List[dict] = None) -> str:
    """
    Add relevant STCC protocol context to patient symptoms.

    Args:
        symptoms: Raw patient symptom description
        protocols: List of parsed protocols (default: auto-load)

    Returns:
        Enhanced prompt with protocol context
    """
    if protocols is None:
        protocols = load_protocols()

    keywords = extract_keywords(symptoms)

    # Find matching protocols
    relevant_protocols = []
    for protocol in protocols:
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
            for section in protocol["sections"][:3]:
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
