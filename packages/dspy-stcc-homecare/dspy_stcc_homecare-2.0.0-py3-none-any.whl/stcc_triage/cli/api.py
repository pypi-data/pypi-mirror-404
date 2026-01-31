"""
CLI command for launching the FastAPI server.

Entry point for stcc-api command.
"""

import argparse


def main():
    """Launch the FastAPI server."""
    parser = argparse.ArgumentParser(
        description="Launch STCC Triage API server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    # Launch uvicorn server
    import uvicorn
    uvicorn.run(
        "stcc_triage.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
