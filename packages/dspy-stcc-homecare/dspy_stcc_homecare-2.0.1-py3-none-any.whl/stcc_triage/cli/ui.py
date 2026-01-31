"""
CLI command for launching the Streamlit UI.

Entry point for stcc-ui command.
"""


def main():
    """Launch the Streamlit UI."""
    import streamlit.web.cli as stcli
    import sys
    from pathlib import Path

    # Get path to Streamlit app
    app_path = Path(__file__).parent.parent / "ui" / "app.py"

    # Launch Streamlit
    sys.argv = ["streamlit", "run", str(app_path)]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
