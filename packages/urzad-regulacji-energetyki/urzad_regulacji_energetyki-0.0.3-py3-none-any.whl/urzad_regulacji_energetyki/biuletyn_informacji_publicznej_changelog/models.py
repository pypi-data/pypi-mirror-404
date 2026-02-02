"""Data models for Public Information Bulletin changes."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Types of changes in the Public Information Bulletin."""

    PUBLICATION = "publication"
    UPDATE = "update"
    REMOVAL = "removal"
    MODIFICATION = "modification"


class BulletinChange(BaseModel):
    """Model representing a change in the Public Information Bulletin."""

    id: str = Field(..., description="Unique identifier of the change")
    title: str = Field(..., description="Title of the published document or change")
    description: Optional[str] = Field(None, description="Description of the change")
    change_type: ChangeType = Field(..., description="Type of change")
    date_published: datetime = Field(..., description="Date when the change was published")
    date_modified: Optional[datetime] = Field(None, description="Date when the change was last modified")
    url: Optional[str] = Field(None, description="URL to the bulletin entry")
    category: Optional[str] = Field(None, description="Category of the bulletin entry")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the change")

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True
