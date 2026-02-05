"""
Claude Code Skills for Tiger ID Investigation System.

Skills are prompt-based workflows that leverage Claude's reasoning capabilities.
They complement MCP servers by handling tasks that require:
- Complex reasoning with Claude's judgment
- Multi-step prompt workflows
- Template-based generation with context
- Natural language understanding

Usage:
    from backend.skills import SkillRegistry, get_skill

    # Get a skill by command
    skill = SkillRegistry.get_skill("/synthesize-evidence")

    # Execute the skill
    result = await skill.execute(context={...})

    # List all available skills
    skills = SkillRegistry.list_skills()
"""

from typing import Dict, List, Optional, Type
from backend.skills.base_skill import (
    BaseSkill,
    SkillDefinition,
    SkillParameter,
    SkillCategory
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SkillRegistry:
    """
    Registry for managing and discovering skills.

    Skills are registered by command (e.g., "/synthesize-evidence") and can be
    retrieved for execution.
    """

    _skills: Dict[str, BaseSkill] = {}
    _skill_classes: Dict[str, Type[BaseSkill]] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, skill_class: Type[BaseSkill]) -> Type[BaseSkill]:
        """
        Register a skill class. Can be used as a decorator.

        Args:
            skill_class: The skill class to register

        Returns:
            The skill class (for decorator usage)

        Example:
            @SkillRegistry.register
            class MySkill(BaseSkill):
                ...
        """
        # Instantiate to get the command
        instance = skill_class()
        command = instance.command

        if command in cls._skill_classes:
            logger.warning(f"Overwriting existing skill registration: {command}")

        cls._skill_classes[command] = skill_class
        cls._skills[command] = instance

        logger.info(f"Registered skill: {command} ({skill_class.__name__})")
        return skill_class

    @classmethod
    def get_skill(cls, command: str) -> Optional[BaseSkill]:
        """
        Get a skill instance by its command.

        Args:
            command: The skill command (e.g., "/synthesize-evidence")

        Returns:
            The skill instance, or None if not found
        """
        cls._ensure_initialized()

        # Normalize command (ensure leading /)
        if not command.startswith("/"):
            command = f"/{command}"

        return cls._skills.get(command)

    @classmethod
    def list_skills(cls) -> List[Dict]:
        """
        List all registered skills.

        Returns:
            List of skill definitions as dictionaries
        """
        cls._ensure_initialized()
        return [skill.to_dict() for skill in cls._skills.values()]

    @classmethod
    def list_by_category(cls, category: SkillCategory) -> List[Dict]:
        """
        List skills filtered by category.

        Args:
            category: The category to filter by

        Returns:
            List of skill definitions in that category
        """
        cls._ensure_initialized()
        return [
            skill.to_dict()
            for skill in cls._skills.values()
            if skill.category == category
        ]

    @classmethod
    def get_commands(cls) -> List[str]:
        """
        Get list of all registered skill commands.

        Returns:
            List of command strings
        """
        cls._ensure_initialized()
        return list(cls._skills.keys())

    @classmethod
    def _ensure_initialized(cls):
        """Ensure all skills are loaded."""
        if not cls._initialized:
            cls._load_skills()
            cls._initialized = True

    @classmethod
    def _load_skills(cls):
        """Load all skill modules to trigger registration."""
        try:
            # Import skill modules to trigger @register decorators
            from backend.skills import evidence_synthesis
            from backend.skills import reasoning_chain
            from backend.skills import facility_investigation
            from backend.skills import report_writer
            from backend.skills import image_advisor
        except ImportError as e:
            # Some skills may not be implemented yet
            logger.debug(f"Some skills not yet available: {e}")


def get_skill(command: str) -> Optional[BaseSkill]:
    """
    Convenience function to get a skill by command.

    Args:
        command: The skill command (e.g., "/synthesize-evidence")

    Returns:
        The skill instance, or None if not found
    """
    return SkillRegistry.get_skill(command)


# Export public interface
__all__ = [
    "BaseSkill",
    "SkillDefinition",
    "SkillParameter",
    "SkillCategory",
    "SkillRegistry",
    "get_skill"
]
