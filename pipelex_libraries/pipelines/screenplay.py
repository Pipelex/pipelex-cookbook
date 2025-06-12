from typing import List, Optional
from pipelex.core.stuff_content import StructuredContent, ListContent
from pydantic import Field

class Character(StructuredContent):
    """A character in the screenplay."""
    name: str = Field(..., description="The character's name")
    age: int = Field(..., description="The character's age")
    description: str = Field(..., description="Physical and personality description")
    background: str = Field(..., description="Character's backstory")
    image_prompt: str = Field(..., description="Prompt for generating character's image")
    image_url: Optional[str] = Field(None, description="URL to the generated character image")

class CharacterList(ListContent[Character]):
    """A list of characters in the screenplay."""

class Scene(StructuredContent):
    """A scene in the screenplay."""
    index: int = Field(..., description="The index of the scene")
    title: str = Field(..., description="Title of the scene")
    location: str = Field(..., description="Where the scene takes place")
    time_of_day: str = Field(..., description="Time of day for the scene")
    description: str = Field(..., description="Detailed description of the scene setting, atmosphere, and initial setup")
    characters_present: List[str] = Field(..., description="Names of characters in the scene")
    action: str = Field(..., description="Initial action that sets up the scene")
    script: str = Field(..., description="The complete scene script in proper screenplay format, including all action descriptions, character movements, and dialogue")
    location_image_prompt: str = Field(..., description="Prompt for generating location image")
    location_image_url: Optional[str] = Field(None, description="URL to the generated location image")

class Chapter(StructuredContent):
    """A chapter in the screenplay."""
    title: str = Field(..., description="Title of the chapter")
    description: str = Field(..., description="Brief description of what happens in this chapter")
    scenes: List[Scene] = Field(..., description="The scenes in this chapter")

class ChapterList(ListContent[Chapter]):
    """A list of chapters in the screenplay."""

class DetailedPitch(StructuredContent):
    """A detailed pitch with character ideas and synopsis."""
    original_pitch: str = Field(..., description="The original pitch")
    expanded_pitch: str = Field(..., description="Expanded version of the pitch with more details")
    character_ideas: List[str] = Field(..., description="Brief descriptions of main characters")
    synopsis: str = Field(..., description="A detailed synopsis of the story")

class Screenplay(StructuredContent):
    """A complete screenplay with characters and scenes."""
    title: str = Field(..., description="The title of the screenplay")
    pitch: DetailedPitch = Field(..., description="The detailed pitch")
    genre: str = Field(..., description="The genre of the screenplay")
    theme: str = Field(..., description="The main theme of the screenplay")
    characters: CharacterList = Field(..., description="The characters in the screenplay")
    chapters: ChapterList = Field(..., description="The chapters in the screenplay")

class FormattedScene(StructuredContent):
    """A scene formatted according to standard screenplay conventions."""
    scene_heading: str = Field(..., description="Scene heading in standard format: INT/EXT. LOCATION - TIME OF DAY")
    action_blocks: List[str] = Field(..., description="List of action paragraphs describing what happens in the scene")
    dialogue_blocks: List[str] = Field(..., description="List of dialogue blocks including character names, parentheticals, and dialogue")
    transitions: List[str] = Field(default_factory=list, description="Scene transitions (e.g., CUT TO:, FADE OUT)")

class FormattedSceneList(ListContent[FormattedScene]):
    """A list of formatted scenes."""

class FormattedScreenplay(StructuredContent):
    """A screenplay formatted according to industry standards."""
    title_page: str = Field(..., description="The formatted title page including title, author, and contact info")
    scenes: FormattedSceneList = Field(..., description="The formatted scenes in sequence") 