"""Skill module for agent capabilities.

Skills are reusable capability bundles that can be loaded and injected
into agent context. Each skill contains instructions, scripts, and references.

Usage:
    Use SkillProvider (from providers module) to inject skills into agent context.
"""
from .types import Skill
from .loader import SkillLoader


__all__ = [
    "Skill",
    "SkillLoader",
]
