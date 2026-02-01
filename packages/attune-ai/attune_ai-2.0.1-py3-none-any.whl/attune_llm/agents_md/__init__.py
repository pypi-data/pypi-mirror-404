"""Markdown Agent System

Define agents in Markdown files with YAML frontmatter for portability.
Integrates with Empathy Framework's UnifiedAgentConfig and model tier system.

Markdown agent format inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from attune_llm.agents_md.loader import AgentLoader
from attune_llm.agents_md.parser import MarkdownAgentParser
from attune_llm.agents_md.registry import AgentRegistry

__all__ = [
    "MarkdownAgentParser",
    "AgentLoader",
    "AgentRegistry",
]
