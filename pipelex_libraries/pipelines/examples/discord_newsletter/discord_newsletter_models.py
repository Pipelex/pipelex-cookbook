from typing import List

import markdown
from pipelex.core.stuff_content import StructuredContent
from pipelex.types import StrEnum
from pydantic import Field, field_validator


class Attachment(StructuredContent):
    """Represents a Discord message attachment"""

    name: str = Field(..., description="Name of the attachment file")
    url: str = Field(..., description="URL of the attachment")


class Embed(StructuredContent):
    """Represents a Discord message embed"""

    title: str = Field(..., description="Title of the embed")
    description: str = Field(..., description="Description of the embed content")
    type: str = Field(..., description="Type of the embed (e.g., article, video)")


class DiscordMessage(StructuredContent):
    """Represents a Discord message within a channel"""

    author: str = Field(..., description="Author of the message")
    content: str = Field(..., description="Content of the message")
    attachments: List[Attachment] = Field(default_factory=list, description="List of message attachments")
    embeds: List[Embed] = Field(default_factory=list, description="List of message embeds")
    link: str = Field(..., description="Link to the message")


class DiscordChannelUpdate(StructuredContent):
    """Represents a Discord channel with its messages"""

    name: str = Field(..., description="Name of the Discord channel")
    position: int = Field(..., description="Position of the channel")
    messages: List[DiscordMessage] = Field(default_factory=list, description="List of messages in the channel")


class ChannelCategory(StrEnum):
    """Represents a category of Discord channels"""

    SHARE = "Share"
    INTRODUCE_YOURSELF = "Introduce Yourself"
    GEOGRAPHIC_HUBS = "Geographic Hubs"
    OTHER = "Other"


class ChannelSummary(StructuredContent):
    """Represents a summarized Discord channel for newsletter inclusion"""

    channel_name: str = Field(..., description="Name of the Discord channel")
    position: int = Field(..., description="Position of the channel for ordering")
    summary_items: List[str] = Field(..., description="Well-written summaries of the channel's activity")

    @field_validator("channel_name", mode="before")
    @classmethod
    def replace_hyphens_with_spaces(cls, v: str) -> str:
        """Replace hyphens with spaces in channel name"""
        return v.replace("-", " ")

    @property
    def category(self) -> ChannelCategory:
        """Categorize channel based on its name"""
        if not self.channel_name:
            raise ValueError("Channel name is empty")

        if self.channel_name in ["Troll"]:
            return ChannelCategory.OTHER

        first_character = self.channel_name[0]

        # Check if first character is a flag emoji (regional indicator symbols)
        # Flag emojis are in the Unicode range U+1F1E6 to U+1F1FF
        if "\U0001f1e6" <= first_character <= "\U0001f1ff":
            return ChannelCategory.GEOGRAPHIC_HUBS

        if self.channel_name == ChannelCategory.INTRODUCE_YOURSELF:
            return ChannelCategory.INTRODUCE_YOURSELF
        else:
            return ChannelCategory.SHARE

    @property
    def summary_items_as_html(self) -> List[str]:
        """Convert summary items to HTML"""
        return [markdown.markdown(item) for item in self.summary_items]
