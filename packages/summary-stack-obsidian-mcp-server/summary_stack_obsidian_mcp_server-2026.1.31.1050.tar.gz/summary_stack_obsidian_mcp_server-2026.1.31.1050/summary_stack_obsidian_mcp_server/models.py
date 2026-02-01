"""Pydantic models for the MCP server."""

from pydantic import BaseModel, Field


class RelationshipData(BaseModel):
    """Relationship between summary stacks for backlink creation."""

    target_summary_stack_id: str = Field(description="UUID of the related summary stack")
    target_title: str = Field(description="Title of the related note")


class ObsidianManifestResult(BaseModel):
    """Result from API containing note data for local vault writing."""

    summary_stack_id: str = Field(description="UUID of the summary stack")
    title: str = Field(description="Note title")
    filename: str = Field(description="Suggested filename (with .md extension)")
    markdown_content: str = Field(description="Full markdown content with frontmatter embedded")
    concepts: list[str] = Field(default_factory=list, description="Key concepts from the content")
    themes: list[str] = Field(default_factory=list, description="Themes identified in the content")
    relationships: list[RelationshipData] = Field(default_factory=list, description="Related summary stacks")
