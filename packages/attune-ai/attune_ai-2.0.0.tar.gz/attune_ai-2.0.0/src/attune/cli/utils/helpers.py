"""Helper utilities for CLI commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from pathlib import Path


def _file_exists(path: str) -> bool:
    """Check if a file exists.

    Args:
        path: File path to check

    Returns:
        True if file exists, False otherwise
    """
    return Path(path).exists()


def _show_achievements(engine) -> None:
    """Show user achievements based on usage.

    Args:
        engine: Engine instance with stats
    """
    stats = engine.get_stats()

    achievements = []
    total_cmds = stats.get("total_commands", 0)
    cmd_counts = stats.get("command_counts", {})

    # Check achievements
    if total_cmds >= 1:
        achievements.append(("First Steps", "Ran your first command"))
    if total_cmds >= 10:
        achievements.append(("Getting Started", "Ran 10+ commands"))
    if total_cmds >= 50:
        achievements.append(("Power User", "Ran 50+ commands"))
    if total_cmds >= 100:
        achievements.append(("Expert", "Ran 100+ commands"))

    if cmd_counts.get("learn", 0) >= 1:
        achievements.append(("Pattern Learner", "Learned from git history"))
    if cmd_counts.get("sync-claude", 0) >= 1:
        achievements.append(("Claude Whisperer", "Synced patterns to Claude"))
    if cmd_counts.get("morning", 0) >= 5:
        achievements.append(("Early Bird", "Used morning briefing 5+ times"))
    if cmd_counts.get("ship", 0) >= 10:
        achievements.append(("Quality Shipper", "Used pre-commit checks 10+ times"))
    if cmd_counts.get("health", 0) >= 1 and cmd_counts.get("fix-all", 0) >= 1:
        achievements.append(("Code Doctor", "Used health checks and fixes"))

    if stats.get("patterns_learned", 0) >= 10:
        achievements.append(("Pattern Master", "Learned 10+ patterns"))

    if stats.get("days_active", 0) >= 7:
        achievements.append(("Week Warrior", "Active for 7+ days"))
    if stats.get("days_active", 0) >= 30:
        achievements.append(("Monthly Maven", "Active for 30+ days"))

    if achievements:
        print("  ACHIEVEMENTS UNLOCKED")
        print("  " + "-" * 30)
        for name, desc in achievements:
            print(f"  * {name}: {desc}")
        print()
