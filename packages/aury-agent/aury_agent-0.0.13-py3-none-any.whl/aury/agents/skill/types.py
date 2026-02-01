"""Skill data types."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass
class Skill:
    """Skill definition.
    
    A skill represents a reusable capability that can be loaded into an agent.
    Skills are defined by SKILL.md files with YAML frontmatter.
    
    Attributes:
        name: Unique identifier (lowercase + hyphens, ≤64 chars)
        description: Description and trigger conditions (≤1024 chars)
        path: Path to SKILL.md file
        source: Origin of the skill (user/project/system)
        license: Optional license
        allowed_tools: Pre-authorized tools for this skill
        metadata: Additional metadata from frontmatter
    """
    name: str
    description: str
    path: Path
    source: Literal["user", "project", "system"]
    
    # Optional metadata
    license: str | None = None
    allowed_tools: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Runtime (lazy loaded)
    _content: str | None = field(default=None, repr=False)
    
    async def load_content(self) -> str:
        """Load full content (Progressive Disclosure).
        
        Lazily loads the body content of SKILL.md when needed.
        """
        if self._content is None:
            self._content = await self._read_body()
        return self._content
    
    async def _read_body(self) -> str:
        """Read SKILL.md body (after frontmatter)."""
        def _read() -> str:
            text = self.path.read_text(encoding="utf-8")
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
            return text
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _read)
    
    def get_resource_path(self, relative: str) -> Path:
        """Get absolute path for a resource relative to skill directory.
        
        Args:
            relative: Relative path (e.g., "scripts/helper.py")
            
        Returns:
            Absolute path to the resource
        """
        return self.path.parent / relative
    
    def has_script(self, name: str) -> bool:
        """Check if skill has a specific script."""
        script_path = self.get_resource_path(f"scripts/{name}")
        return script_path.exists()
    
    def has_reference(self, name: str) -> bool:
        """Check if skill has a specific reference document."""
        ref_path = self.get_resource_path(f"references/{name}")
        return ref_path.exists()


__all__ = ["Skill"]
