"""Pydantic models for M365 Roadmap features."""

from pydantic import BaseModel, Field


class RoadmapFeature(BaseModel):
    """Represents a single feature from the M365 Roadmap API."""

    id: str = Field(description="Unique Roadmap ID")
    title: str = Field(description="Feature title")
    description: str = Field(description="Feature description (HTML/text)")
    status: str | None = Field(
        default=None,
        description="Feature status: In development, Rolling out, or Launched",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Product tags (e.g., Microsoft Teams, SharePoint)",
    )
    cloud_instances: list[str] = Field(
        default_factory=list,
        description="Cloud availability (e.g., Worldwide, GCC, GCC High, DoD)",
    )
    public_disclosure_date: str | None = Field(
        default=None,
        description="Estimated release date (e.g., August CY2026)",
    )
    created: str | None = Field(
        default=None,
        description="Date the feature was added to the roadmap",
    )
    modified: str | None = Field(
        default=None,
        description="Date the feature was last modified",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for tool output."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "tags": self.tags,
            "cloud_instances": self.cloud_instances,
            "public_disclosure_date": self.public_disclosure_date,
            "created": self.created,
            "modified": self.modified,
        }
