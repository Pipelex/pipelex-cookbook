from typing import List, Optional

from pipelex.core.stuff_content import StructuredContent
from pydantic import Field


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


class DiscordArticle(StructuredContent):
    """Represents a Discord channel with its messages for newsletter generation"""

    name: str = Field(..., description="Name of the Discord channel")
    position: int = Field(..., description="Position of the channel")
    messages: List[DiscordMessage] = Field(default_factory=list, description="List of messages in the channel")
