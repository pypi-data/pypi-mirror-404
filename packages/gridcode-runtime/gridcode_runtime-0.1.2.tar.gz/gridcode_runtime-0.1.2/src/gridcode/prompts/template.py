"""Prompt template loading and parsing.

This module handles loading prompt templates from markdown files with YAML frontmatter,
following Claude Code's prompt file format.
"""

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    """Metadata extracted from prompt template frontmatter."""

    name: str
    description: str = ""
    cc_version: str = Field(default="0.0.0", alias="ccVersion")
    variables: list[str] = Field(default_factory=list)


class PromptTemplate(BaseModel):
    """Represents a prompt template with metadata and content."""

    metadata: PromptMetadata
    content: str
    file_path: Path | None = None

    @classmethod
    def from_file(cls, file_path: Path) -> "PromptTemplate":
        """Load a prompt template from a markdown file.

        Args:
            file_path: Path to the markdown file with HTML comment frontmatter

        Returns:
            PromptTemplate instance

        Raises:
            ValueError: If file format is invalid
        """
        content = file_path.read_text(encoding="utf-8")
        return cls.from_string(content, file_path)

    @classmethod
    def from_string(cls, content: str, file_path: Path | None = None) -> "PromptTemplate":
        """Parse a prompt template from string content.

        Expected format:
        <!--
        name: 'Prompt Name'
        description: Description text
        ccVersion: 2.1.20
        variables:
          - VAR1
          - VAR2
        -->
        Prompt content here with ${VAR1} and ${VAR2}

        Args:
            content: The full file content
            file_path: Optional path for reference

        Returns:
            PromptTemplate instance

        Raises:
            ValueError: If frontmatter is missing or invalid
        """
        # Extract HTML comment frontmatter
        frontmatter_pattern = r"<!--\s*\n(.*?)\n-->"
        match = re.search(frontmatter_pattern, content, re.DOTALL)

        if not match:
            raise ValueError("No HTML comment frontmatter found in template")

        frontmatter_text = match.group(1)
        prompt_content = content[match.end() :].strip()

        # Parse YAML frontmatter
        try:
            metadata_dict = yaml.safe_load(frontmatter_text)
            metadata = PromptMetadata(**metadata_dict)
        except (yaml.YAMLError, Exception) as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}") from e

        return cls(metadata=metadata, content=prompt_content, file_path=file_path)

    def get_variables(self) -> list[str]:
        """Get list of variables declared in metadata."""
        return self.metadata.variables.copy()
