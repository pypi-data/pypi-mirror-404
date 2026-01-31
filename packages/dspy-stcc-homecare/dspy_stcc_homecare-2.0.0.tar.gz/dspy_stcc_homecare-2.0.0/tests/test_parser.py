"""
Tests for STCC protocol parser.

Covers expected use, edge cases, and failure cases.
"""

from pathlib import Path

import pytest

from protocols.parser import parse_all_protocols, parse_stcc_markdown


STCC_DIR = Path(__file__).resolve().parent.parent / "protocols" / "STCC-chinese"


class TestParseAllProtocols:
    """Expected use: parse the full STCC-chinese directory."""

    def test_parses_all_225_protocols(self):
        """parse_all_protocols returns 225 protocols from the default directory."""
        protocols = parse_all_protocols(STCC_DIR)
        assert len(protocols) == 225

    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Failure case: nonexistent directory returns empty list."""
        missing = tmp_path / "does_not_exist"
        protocols = parse_all_protocols(missing)
        assert protocols == []


class TestParseStccMarkdown:
    """Edge case: verify a specific protocol parses correctly."""

    def test_chest_pain_protocol_name(self):
        """Chest_Pain.md should parse with the correct protocol name."""
        chest_pain_file = STCC_DIR / "Chest_Pain.md"
        protocol = parse_stcc_markdown(chest_pain_file)
        assert protocol.protocol_name == "胸痛"

    def test_chest_pain_has_emergency_section(self):
        """Chest_Pain.md should have an emergency (section A) entry."""
        chest_pain_file = STCC_DIR / "Chest_Pain.md"
        protocol = parse_stcc_markdown(chest_pain_file)

        section_ids = [s.section_id for s in protocol.sections]
        assert "A" in section_ids

        section_a = next(s for s in protocol.sections if s.section_id == "A")
        assert section_a.urgency_level == "emergency"

    def test_chest_pain_has_key_questions(self):
        """Chest_Pain.md should extract key questions from the header."""
        chest_pain_file = STCC_DIR / "Chest_Pain.md"
        protocol = parse_stcc_markdown(chest_pain_file)
        assert len(protocol.key_questions) > 0
