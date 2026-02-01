"""Parser definitions for info commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import info as info_commands


def register_parsers(subparsers):
    """Register info command parsers.

    Args:
        subparsers: ArgumentParser subparsers object
    """
    # info command
    parser_info = subparsers.add_parser("info", help="Display framework information")
    parser_info.add_argument("--config", help="Path to config file")
    parser_info.set_defaults(func=info_commands.cmd_info)

    # frameworks command
    parser_frameworks = subparsers.add_parser("frameworks", help="List agent frameworks")
    parser_frameworks.add_argument("--all", action="store_true", help="Show all frameworks")
    parser_frameworks.add_argument("--recommend", help="Recommend for use case")
    parser_frameworks.add_argument("--json", action="store_true", help="Output as JSON")
    parser_frameworks.set_defaults(func=info_commands.cmd_frameworks)
