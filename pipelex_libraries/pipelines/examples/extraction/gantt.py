# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

from datetime import datetime
from typing import List, Literal, Optional

from pipelex.core.stuff_content import ListContent, StructuredContent, TextContent
from pydantic import field_validator


class TaskNames(ListContent[TextContent]):
    pass


class GanttTaskDetails(StructuredContent):
    """Do not include timezone in the dates."""

    name: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]

    @field_validator("start_date", "end_date")
    @classmethod
    def remove_tzinfo(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            return v.replace(tzinfo=None)
        return v


class Milestone(StructuredContent):
    name: str
    date: datetime

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
