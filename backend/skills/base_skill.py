"""Base skill class for Claude Code skills."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SkillCategory(str, Enum):
    """Categories of skills for organization and discovery."""
    ANALYSIS = "analysis"
    RESEARCH = "research"
    REPORTING = "reporting"
    REASONING = "reasoning"
    QUALITY = "quality"


@dataclass
class SkillParameter:
    """Definition of a skill parameter."""
    name: str
    description: str
    type: str  # "string", "number", "boolean", "array", "object"
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class SkillDefinition:
    """Complete definition of a skill."""
    name: str
    description: str
    command: str  # e.g., "/synthesize-evidence"
    category: SkillCategory
    parameters: List[SkillParameter] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class BaseSkill(ABC):
    """
    Base class for all Claude Code skills.

    Skills are prompt-based workflows that leverage Claude's reasoning capabilities.
    They differ from MCP tools in that they:
    - Use natural language prompts as templates
    - Leverage Claude's judgment for complex reasoning
    - Generate human-readable outputs
    - Can be invoked via /command syntax

    Subclasses must implement:
    - get_definition(): Returns SkillDefinition describing the skill
    - get_prompt_template(): Returns the prompt template string
    - execute(): Executes the skill with given context
    """

    def __init__(self):
        """Initialize the skill."""
        self._definition = self.get_definition()
        self._prompt_template = self.get_prompt_template()
        logger.info(f"Initialized skill: {self._definition.name}")

    @property
    def name(self) -> str:
        """Get skill name."""
        return self._definition.name

    @property
    def command(self) -> str:
        """Get skill command (e.g., '/synthesize-evidence')."""
        return self._definition.command

    @property
    def category(self) -> SkillCategory:
        """Get skill category."""
        return self._definition.category

    @property
    def description(self) -> str:
        """Get skill description."""
        return self._definition.description

    @abstractmethod
    def get_definition(self) -> SkillDefinition:
        """
        Return the skill definition.

        Returns:
            SkillDefinition with name, description, command, category, and parameters
        """
        pass

    @abstractmethod
    def get_prompt_template(self) -> str:
        """
        Return the prompt template string.

        The template can use {variable_name} placeholders that will be
        filled in from the context dictionary passed to execute().

        Returns:
            Prompt template string
        """
        pass

    @abstractmethod
    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the skill with the given context.

        Args:
            context: Dictionary containing data to inject into the prompt template
            **kwargs: Additional execution options

        Returns:
            Dictionary containing:
                - success: bool
                - output: str (the generated content)
                - metadata: dict (optional additional data)
                - error: str (if success is False)
        """
        pass

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build the final prompt by injecting context into the template.

        Args:
            context: Dictionary of values to inject

        Returns:
            Formatted prompt string
        """
        try:
            return self._prompt_template.format(**context)
        except KeyError as e:
            logger.error(f"Missing context key in prompt template: {e}")
            raise ValueError(f"Missing required context key: {e}")

    def validate_context(self, context: Dict[str, Any]) -> List[str]:
        """
        Validate that required parameters are present in context.

        Args:
            context: Context dictionary to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        for param in self._definition.parameters:
            if param.required and param.name not in context:
                errors.append(f"Missing required parameter: {param.name}")

            if param.name in context and param.enum:
                value = context[param.name]
                if value not in param.enum:
                    errors.append(
                        f"Invalid value for {param.name}: {value}. "
                        f"Must be one of: {param.enum}"
                    )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert skill definition to dictionary for API responses.

        Returns:
            Dictionary representation of the skill
        """
        return {
            "name": self._definition.name,
            "description": self._definition.description,
            "command": self._definition.command,
            "category": self._definition.category.value,
            "parameters": [
                {
                    "name": p.name,
                    "description": p.description,
                    "type": p.type,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum
                }
                for p in self._definition.parameters
            ],
            "examples": self._definition.examples
        }
