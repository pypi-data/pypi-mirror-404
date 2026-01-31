"""
CLI command for parsing STCC protocols.

Entry point for stcc-parse-protocols command.
"""


def main():
    """Parse STCC protocols from markdown to JSON."""
    from stcc_triage.protocols.parser import parse_all_protocols
    from stcc_triage.core.paths import get_protocols_dir

    print("Parsing STCC Protocols")
    print("=" * 60)

    try:
        stcc_dir = get_protocols_dir()
        print(f"Source: {stcc_dir}")

        protocols = parse_all_protocols(stcc_dir)

        print(f"\n✓ Successfully parsed {len(protocols)} protocols")
        print("\nProtocols saved to: protocols/protocols.json")

    except Exception as e:
        print(f"\n✗ Error parsing protocols: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
