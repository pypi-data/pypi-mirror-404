"""CLI Commands Package for Meta-Workflows.

Organized command modules for meta-workflow system.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import typer

# Create Typer app for meta-workflow commands
meta_workflow_app = typer.Typer(
    name="meta-workflow",
    help="Meta-workflow system for dynamic agent team generation",
    no_args_is_help=True,
)

# Import all commands (they will auto-register with meta_workflow_app via decorators)
from .agent_commands import create_agent, create_team
from .analytics_commands import (
    cleanup_executions,
    list_runs,
    show_analytics,
    show_execution,
)
from .config_commands import show_migration_guide, suggest_defaults_cmd
from .memory_commands import search_memory, show_session_stats
from .template_commands import generate_plan_cmd, inspect_template, list_templates
from .workflow_commands import detect_intent, natural_language_run, run_workflow

__all__ = [
    # Typer app
    "meta_workflow_app",
    # Template commands
    "list_templates",
    "inspect_template",
    "generate_plan_cmd",
    # Workflow commands
    "run_workflow",
    "natural_language_run",
    "detect_intent",
    # Analytics commands
    "show_analytics",
    "list_runs",
    "show_execution",
    "cleanup_executions",
    # Memory commands
    "search_memory",
    "show_session_stats",
    # Config commands
    "suggest_defaults_cmd",
    "show_migration_guide",
    # Agent commands
    "create_agent",
    "create_team",
]
