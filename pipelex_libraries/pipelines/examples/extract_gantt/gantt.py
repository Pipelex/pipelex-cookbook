from datetime import datetime
from typing import List, Literal, Optional

from pipelex.core.stuff_content import ListContent, StructuredContent, TextContent
from pydantic import field_validator


class TaskNames(ListContent[TextContent]):
    pass


class GanttTaskDetails(StructuredContent):
    """Do not include timezone in the dates."""

    name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("start_date", "end_date")
    @classmethod
    def remove_tzinfo(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            return v.replace(tzinfo=None)
        return v


class Milestone(StructuredContent):
    name: str
    date: Optional[datetime]

    @field_validator("date")
    @classmethod
    def remove_tzinfo(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            return v.replace(tzinfo=None)
        return v


class GanttChart(StructuredContent):
    tasks: Optional[List[GanttTaskDetails]]
    milestones: Optional[List[Milestone]]


class GanttTimescaleDescription(StructuredContent):
    unit: Literal["days", "weeks", "months", "years"]
