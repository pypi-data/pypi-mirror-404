"""
STCC Protocol Parser.

Parses Schmitt-Thompson Clinical Content (STCC) markdown files
into structured JSON format for DSPy consumption.
"""

from pathlib import Path
import json
import re
from typing import List
from pydantic import BaseModel, Field


class ProtocolSection(BaseModel):
    """Single decision point in triage protocol."""

    section_id: str  # "A", "B", "C", "D"
    urgency_level: str  # "emergency", "urgent", "moderate", "home_care"
    conditions: List[str]  # Symptom criteria
    action: str  # What to do (call ambulance, seek care, home care)


class STCCProtocol(BaseModel):
    """Complete STCC clinical protocol."""

    protocol_name: str
    category: str  # e.g., "Chest Pain", "Abdominal Pain"
    key_questions: List[str]  # 关键问题
    sections: List[ProtocolSection]
    red_flags: List[str]  # Critical symptoms requiring immediate action


def parse_stcc_markdown(filepath: Path) -> STCCProtocol:
    """
    Parse single STCC markdown file into structured protocol.

    Pattern recognition:
    1. Extract protocol name from # header
    2. Parse key questions (关键问题:)
    3. Identify sections A, B, C, D
    4. Extract conditions for each section (● bullets)
    5. Extract actions (是 "action text")
    6. Flag section A symptoms as red flags

    Args:
        filepath: Path to STCC markdown file

    Returns:
        Structured STCCProtocol object
    """
    content = filepath.read_text(encoding="utf-8")

    # Extract protocol name from first heading
    name_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    protocol_name = name_match.group(1).strip() if name_match else filepath.stem

    # Parse key questions (关键问题)
    key_q_match = re.search(r"关键问题[：:]\s*(.+)", content)
    key_questions = []
    if key_q_match:
        questions_text = key_q_match.group(1)
        key_questions = [q.strip() for q in questions_text.split("，") if q.strip()]

    # Parse sections (A, B, C, D) from "评估与行动" or similar sections
    sections = []

    # Map section IDs to urgency levels based on STCC pattern
    urgency_map = {
        "A": "emergency",  # 呼叫救护车 (Call ambulance)
        "B": "urgent",  # 立即寻求紧急医疗 (Seek emergency care)
        "C": "moderate",  # 2-4小时内就医 (See doctor within 2-4 hours)
        "D": "home_care",  # 家庭护理 (Home care)
    }

    # Find section pattern: "A. 是否存在以下任何情况？"
    section_pattern = r"([A-D])\.\s*是否存在以下任何情况？"
    section_matches = list(re.finditer(section_pattern, content))

    for i, match in enumerate(section_matches):
        section_id = match.group(1)
        start_pos = match.end()

        # Find end position (next section or end of assessment block)
        if i < len(section_matches) - 1:
            end_pos = section_matches[i + 1].start()
        else:
            # Look for next major section marker or end of file
            next_section = re.search(r"\n## ", content[start_pos:])
            end_pos = (
                start_pos + next_section.start() if next_section else len(content)
            )

        section_text = content[start_pos:end_pos]

        # Extract conditions (bullet points ●)
        conditions = []
        bullet_pattern = r"●(.+?)(?=\n●|\n\n|是\\s*[\"""]|否\\s*|$)"
        for cond_match in re.finditer(bullet_pattern, section_text, re.DOTALL):
            condition = cond_match.group(1).strip()
            # Clean up multi-line conditions
            condition = re.sub(r"\s+", " ", condition)
            if condition:
                conditions.append(condition)

        # Extract action (是 "action text")
        action = ""
        action_match = re.search(r'是\\s*[\"""](.+?)[\"""]', section_text)
        if action_match:
            action = action_match.group(1).strip()

        if conditions:  # Only add if we found conditions
            sections.append(
                ProtocolSection(
                    section_id=section_id,
                    urgency_level=urgency_map.get(section_id, "unknown"),
                    conditions=conditions,
                    action=action,
                )
            )

    # Section A conditions are red flags (emergency symptoms)
    red_flags = sections[0].conditions if sections else []

    return STCCProtocol(
        protocol_name=protocol_name,
        category=protocol_name,
        key_questions=key_questions,
        sections=sections,
        red_flags=red_flags,
    )


def parse_all_protocols(
    stcc_dir: Path = None,
    output_path: Path = None,
) -> List[STCCProtocol]:
    """
    Parse all STCC protocols and save to JSON.

    Args:
        stcc_dir: Directory containing STCC markdown files (default: package data)
        output_path: Output JSON file path (default: repo root protocols/protocols.json)

    Returns:
        List of parsed STCCProtocol objects
    """
    # Use package data directory if not specified
    if stcc_dir is None:
        from stcc_triage.core.paths import get_protocols_dir
        stcc_dir = get_protocols_dir()

    protocols = []
    errors = []

    for md_file in stcc_dir.glob("*.md"):
        try:
            protocol = parse_stcc_markdown(md_file)
            protocols.append(protocol)
        except Exception as e:
            errors.append(f"Error parsing {md_file.name}: {e}")

    if errors:
        print("\n".join(errors))

    # Save to JSON - default to repo root for development
    if output_path is None:
        # Try repo root first (for development workflow)
        repo_root = Path(__file__).parent.parent.parent
        output_path = repo_root / "protocols" / "protocols.json"
        output_path.parent.mkdir(exist_ok=True, parents=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            [p.model_dump() for p in protocols],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Parsed {len(protocols)} protocols, saved to {output_path}")
    return protocols


if __name__ == "__main__":
    from stcc_triage.core.paths import get_protocols_dir

    stcc_dir = get_protocols_dir()
    if not stcc_dir.exists():
        print(f"STCC directory not found at {stcc_dir}")
        print("Expected: stcc_triage/data/protocols/STCC-chinese/ (225 markdown files)")
        raise SystemExit(1)

    protocols = parse_all_protocols(stcc_dir)
    print(f"\nSuccessfully parsed {len(protocols)} STCC protocols")
