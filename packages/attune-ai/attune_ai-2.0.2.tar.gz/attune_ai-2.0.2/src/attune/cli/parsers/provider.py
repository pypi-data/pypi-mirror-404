"""Parser definitions for provider commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import provider


def register_parsers(subparsers):
    """Register provider command parsers (Anthropic-only as of v5.0.0).

    Args:
        subparsers: ArgumentParser subparsers object from main parser
    """
    # Provider parent command
    parser_provider = subparsers.add_parser(
        "provider",
        help="Configure Claude/Anthropic provider",
    )
    provider_sub = parser_provider.add_subparsers(dest="provider_command", required=True)

    # Provider show command
    p_show = provider_sub.add_parser(
        "show",
        help="Show current provider configuration",
    )
    p_show.set_defaults(func=provider.cmd_provider_show)

    # Provider set command
    p_set = provider_sub.add_parser(
        "set",
        help="Set default provider (must be 'anthropic')",
    )
    p_set.add_argument(
        "name",
        choices=["anthropic"],
        help="Provider name (anthropic only)",
    )
    p_set.set_defaults(func=provider.cmd_provider_set)
