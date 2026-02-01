"""Commands Module for Empathy Framework

Provides command loading, parsing, and execution with integration
to hooks, context management, and learning modules.

Architectural patterns inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from attune_llm.commands.context import (
                                                  CommandContext,
                                                  CommandExecutor,
                                                  create_command_context,
)
from attune_llm.commands.loader import (
                                                  CommandLoader,
                                                  get_default_commands_directory,
                                                  load_commands_from_paths,
)
from attune_llm.commands.models import (
                                                  CommandCategory,
                                                  CommandConfig,
                                                  CommandMetadata,
                                                  CommandResult,
)
from attune_llm.commands.parser import CommandParser
from attune_llm.commands.registry import CommandRegistry

__all__ = [
    # Models
    "CommandCategory",
    "CommandConfig",
    "CommandContext",
    "CommandMetadata",
    "CommandResult",
    # Parser
    "CommandParser",
    # Loader
    "CommandLoader",
    "get_default_commands_directory",
    "load_commands_from_paths",
    # Registry
    "CommandRegistry",
    # Context & Executor
    "CommandExecutor",
    "create_command_context",
]
