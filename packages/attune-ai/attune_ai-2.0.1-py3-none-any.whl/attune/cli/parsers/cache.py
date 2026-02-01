"""Argument parser for cache commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""


def register_parsers(subparsers):
    """Register cache command parsers.

    Args:
        subparsers: Subparser object from main argument parser

    Returns:
        None: Adds cache subparser with stats and clear subcommands
    """
    from ..commands.cache import cmd_cache_clear, cmd_cache_stats
    # Main cache command
    cache_parser = subparsers.add_parser(
        "cache",
        help="Cache monitoring and management",
        description="Monitor prompt caching performance and cost savings",
    )

    # Cache subcommands
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)

    # cache stats command
    stats_parser = cache_subparsers.add_parser(
        "stats",
        help="Show cache performance statistics",
        description="Display prompt caching metrics including hit rate and cost savings",
    )

    stats_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )

    stats_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    stats_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed token metrics",
    )

    stats_parser.set_defaults(func=cmd_cache_stats)

    # cache clear command (placeholder)
    clear_parser = cache_subparsers.add_parser(
        "clear",
        help="Clear cache (note: Anthropic cache is server-side with 5min TTL)",
        description="Information about cache clearing",
    )

    clear_parser.set_defaults(func=cmd_cache_clear)
