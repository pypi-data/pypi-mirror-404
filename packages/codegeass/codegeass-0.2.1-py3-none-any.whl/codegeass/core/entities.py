"""Domain entities for CodeGeass.

This module re-exports all entities from the entities/ package.
Each entity is now in its own module for single-responsibility.

Entities:
- Skill: Claude Code skill reference
- Template: Task template with defaults
- Prompt: Structured prompt with system/task/context
- Task: Scheduled task configuration
- Project: Multi-project registration
"""

from codegeass.core.entities.project import Project
from codegeass.core.entities.prompt import Prompt
from codegeass.core.entities.skill import Skill
from codegeass.core.entities.task import Task
from codegeass.core.entities.template import Template

__all__ = [
    "Project",
    "Prompt",
    "Skill",
    "Task",
    "Template",
]
