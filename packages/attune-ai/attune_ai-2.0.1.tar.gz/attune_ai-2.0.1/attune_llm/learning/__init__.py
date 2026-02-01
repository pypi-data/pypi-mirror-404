"""Continuous Learning Module for Empathy Framework

Automatic pattern extraction from sessions to enable learning and improvement.
Identifies valuable patterns from user interactions for future application.

Architectural patterns inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from attune_llm.learning.evaluator import SessionEvaluator, SessionQuality
from attune_llm.learning.extractor import (
                                                    ExtractedPattern,
                                                    PatternCategory,
                                                    PatternExtractor,
)
from attune_llm.learning.storage import LearnedSkill, LearnedSkillsStorage

__all__ = [
    "ExtractedPattern",
    "LearnedSkill",
    "LearnedSkillsStorage",
    "PatternCategory",
    "PatternExtractor",
    "SessionEvaluator",
    "SessionQuality",
]
