"""Parser definitions for orchestrate commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import orchestrate


def register_parsers(subparsers):
    """Register orchestrate command parsers.

    Args:
        subparsers: ArgumentParser subparsers object from main parser
    """
    # Orchestrate command
    parser_orchestrate = subparsers.add_parser(
        "orchestrate",
        help="Run meta-orchestration workflows (release-prep, health-check)",
    )
    parser_orchestrate.add_argument(
        "workflow",
        choices=["release-prep", "health-check", "test-coverage"],
        help="Orchestration workflow to run",
    )
    parser_orchestrate.add_argument(
        "--path",
        default=".",
        help="Project path (for release-prep)",
    )
    parser_orchestrate.add_argument(
        "--mode",
        choices=["daily", "weekly", "release"],
        help="Health check mode (for health-check)",
    )
    parser_orchestrate.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (for health-check)",
    )
    parser_orchestrate.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser_orchestrate.add_argument(
        "--min-coverage",
        type=int,
        help="Minimum test coverage percentage (for release-prep)",
    )
    parser_orchestrate.add_argument(
        "--min-quality",
        type=int,
        help="Minimum quality score (for release-prep)",
    )
    parser_orchestrate.add_argument(
        "--max-critical",
        type=int,
        help="Maximum critical issues allowed (for release-prep)",
    )
    parser_orchestrate.set_defaults(func=orchestrate.cmd_orchestrate)
