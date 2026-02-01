"""Parser definitions for status and health commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import status as status_commands


def register_parsers(subparsers):
    """Register status command parsers.

    Args:
        subparsers: ArgumentParser subparsers object
    """
    # status command
    parser_status = subparsers.add_parser("status", help="Show project status")
    parser_status.add_argument("--patterns-dir", default="./patterns", help="Patterns directory")
    parser_status.add_argument("--project-root", default=".", help="Project root")
    parser_status.add_argument(
        "--inactivity", type=int, default=30, help="Inactivity threshold (minutes)"
    )
    parser_status.add_argument("--full", action="store_true", help="Show all items")
    parser_status.add_argument("--json", action="store_true", help="Output as JSON")
    parser_status.add_argument("--select", type=int, help="Select item for action")
    parser_status.add_argument("--force", action="store_true", help="Force show status")
    parser_status.set_defaults(func=status_commands.cmd_status)

    # review command (deprecated)
    parser_review = subparsers.add_parser("review", help="Code review (deprecated)")
    parser_review.set_defaults(func=status_commands.cmd_review)

    # health command
    parser_health = subparsers.add_parser("health", help="Run health checks")
    parser_health.add_argument("--check", help="Specific check (lint/type/format/test)")
    parser_health.add_argument("--deep", action="store_true", help="Run all checks")
    parser_health.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser_health.add_argument("--dry-run", action="store_true", help="Preview fixes only")
    parser_health.add_argument(
        "--interactive", action="store_true", help="Interactive fix mode"
    )
    parser_health.add_argument("--project-root", default=".", help="Project root")
    parser_health.add_argument("--details", action="store_true", help="Show details")
    parser_health.add_argument("--full", action="store_true", help="Show all details")
    parser_health.add_argument("--trends", type=int, help="Show trends (days)")
    parser_health.add_argument("--json", action="store_true", help="Output as JSON")
    parser_health.set_defaults(func=status_commands.cmd_health)
