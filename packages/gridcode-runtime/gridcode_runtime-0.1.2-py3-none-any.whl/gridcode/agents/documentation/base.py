"""
Documentation Agents Base Module

Shared types and base classes for documentation agents.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gridcode.agents.base import AgentType, BaseAgent
from gridcode.prompts.composer import PromptComposer


class DocFormat(str, Enum):
    """Documentation output format"""

    MARKDOWN = "markdown"
    OPENAPI = "openapi"
    DOCSTRING = "docstring"
    RST = "rst"


class TargetAudience(str, Enum):
    """Target audience for documentation"""

    DEVELOPERS = "developers"
    ARCHITECTS = "architects"
    OPERATORS = "operators"
    END_USERS = "end_users"


class SkillLevel(str, Enum):
    """Tutorial skill level"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class DocumentSection:
    """A single documentation section"""

    title: str
    content: str
    order: int = 0
    subsections: list["DocumentSection"] = field(default_factory=list)


@dataclass
class DocumentationOutput:
    """Complete documentation output"""

    title: str
    sections: list[DocumentSection] = field(default_factory=list)
    format: DocFormat = DocFormat.MARKDOWN
    source_files: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    summary: str = ""

    def add_section(self, section: DocumentSection) -> None:
        """Add a section to the documentation"""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> dict[str, Any]:
        """Convert output to dictionary"""
        return {
            "title": self.title,
            "format": self.format.value,
            "section_count": self.section_count,
            "source_files": self.source_files,
            "generated_files": self.generated_files,
            "summary": self.summary,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content[:500] + "..." if len(s.content) > 500 else s.content,
                    "order": s.order,
                }
                for s in self.sections
            ],
        }

    def to_markdown(self) -> str:
        """Generate full markdown content"""
        lines = [f"# {self.title}", ""]

        if self.summary:
            lines.append(self.summary)
            lines.append("")

        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

            for subsection in section.subsections:
                lines.append(f"### {subsection.title}")
                lines.append("")
                lines.append(subsection.content)
                lines.append("")

        return "\n".join(lines)


class BaseDocumentationAgent(BaseAgent):
    """
    Base class for documentation agents

    Provides common functionality for documentation generation agents.
    All documentation agents can write files but cannot execute code.
    """

    agent_type = AgentType.PLAN  # Using PLAN as closest match

    # Common tool permissions for documentation agents
    allowed_tools = ["Read", "Glob", "Grep", "Write"]
    forbidden_tools = ["Edit", "Bash", "Task", "AskUserQuestion"]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        output_format: DocFormat = DocFormat.MARKDOWN,
    ):
        """
        Initialize documentation agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            output_format: Default output format
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.output_format = output_format

    async def _create_mock_output(
        self,
        title: str,
        summary: str,
        source_files: list[str],
    ) -> DocumentationOutput:
        """Create mock documentation output for placeholder implementation"""
        await asyncio.sleep(0.05)  # Simulate work

        output = DocumentationOutput(
            title=title,
            format=self.output_format,
            source_files=source_files,
            summary=summary,
        )

        output.add_section(
            DocumentSection(
                title="Overview",
                content="This is a mock documentation section.",
                order=1,
            )
        )

        return output
