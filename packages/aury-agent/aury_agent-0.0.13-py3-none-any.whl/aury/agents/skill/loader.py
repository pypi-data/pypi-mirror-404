"""SkillLoader - Load skills from filesystem."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Literal

import yaml

from .types import Skill


class SkillLoader:
    """Load and manage skills from the filesystem.
    
    Skills are loaded from SKILL.md files with priority:
    1. project/ - Project-level skills (.aury/skills/)
    2. user/ - User-level skills (~/.aury/skills/)
    3. system/ - Built-in skills (framework provided)
    
    Same-named skills: higher priority overrides lower.
    
    Usage:
        loader = SkillLoader()
        await loader.load_from_directory(Path(".aury/skills"), source="project")
        
        skill = loader.get("code-review")
        all_skills = loader.list_all()
    """
    
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
    
    async def load_from_directory(
        self,
        directory: Path,
        source: Literal["user", "project", "system"] = "user",
    ) -> list[Skill]:
        """Load skills from a directory.
        
        Scans for SKILL.md files and loads them.
        
        Args:
            directory: Directory to scan
            source: Source identifier for loaded skills
            
        Returns:
            List of loaded skills
        """
        loaded: list[Skill] = []
        
        if not directory.exists():
            return loaded
        
        for skill_md in directory.rglob("SKILL.md"):
            try:
                skill = await self._load_skill(skill_md, source)
                if skill:
                    if skill.name not in self._skills:
                        self._skills[skill.name] = skill
                        loaded.append(skill)
            except Exception:
                continue
        
        return loaded
    
    async def _load_skill(
        self,
        path: Path,
        source: Literal["user", "project", "system"],
    ) -> Skill | None:
        """Load a single skill from SKILL.md."""
        def _parse() -> tuple[dict[str, Any], str] | None:
            text = path.read_text(encoding="utf-8")
            
            if not text.startswith("---"):
                return None
            
            parts = text.split("---", 2)
            if len(parts) < 3:
                return None
            
            frontmatter = yaml.safe_load(parts[1])
            if not frontmatter:
                return None
            
            return frontmatter, parts[2].strip()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _parse)
        
        if not result:
            return None
        
        frontmatter, body = result
        
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        
        if not name or not description:
            return None
        
        if not re.match(r"^[a-z][a-z0-9-]*$", name) or len(name) > 64:
            return None
        
        allowed_tools = None
        if "allowed_tools" in frontmatter:
            tools_str = frontmatter["allowed_tools"]
            if isinstance(tools_str, str):
                allowed_tools = tools_str.split()
            elif isinstance(tools_str, list):
                allowed_tools = tools_str
        
        return Skill(
            name=name,
            description=description.strip(),
            path=path,
            source=source,
            license=frontmatter.get("license"),
            allowed_tools=allowed_tools,
            metadata={k: v for k, v in frontmatter.items() 
                     if k not in ("name", "description", "license", "allowed_tools")},
            _content=body,
        )
    
    def get(self, name: str) -> Skill | None:
        """Get skill by name."""
        return self._skills.get(name)
    
    def list_all(self) -> list[Skill]:
        """Get all registered skills."""
        return list(self._skills.values())
    
    def match(self, query: str) -> list[Skill]:
        """Fuzzy match skills based on description.
        
        Simple keyword matching - can be enhanced with embeddings.
        """
        query_lower = query.lower()
        matches = []
        
        for skill in self._skills.values():
            desc_lower = skill.description.lower()
            name_lower = skill.name.lower()
            
            query_words = query_lower.split()
            if any(word in desc_lower or word in name_lower for word in query_words):
                matches.append(skill)
        
        return matches
    
    def format_for_prompt(self) -> str:
        """Format skills for system prompt injection.
        
        Returns a markdown-formatted list of available skills.
        """
        if not self._skills:
            return ""
        
        lines = ["## Available Skills\n"]
        
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            desc_first_line = skill.description.split("\n")[0].strip()
            lines.append(f"- **{skill.name}**: {desc_first_line}")
            lines.append(f"  Path: `{skill.path.parent}`")
            
            if skill.allowed_tools:
                lines.append(f"  Tools: {', '.join(skill.allowed_tools)}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear all loaded skills."""
        self._skills.clear()


__all__ = ["SkillLoader"]
