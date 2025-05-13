# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

from enum import StrEnum

from pipelex.core.stuff_content import StructuredContent
from pipelex.tools.misc.model_helpers import ExtraFieldAttribute
from pipelex.tools.utils.string_utils import snake_to_capitalize_first_letter
from pydantic import Field


class ImageCategory(StrEnum):
    GANTT_CHART = "gantt_chart"
    AD_BANNER = "ad_banner"
    FASHION_PHOTO = "fashion_photo"
    INVOICE_SCAN = "invoice_scan"
    # ILLUSTRATION = "illustration"
    # MOODBOARD = "moodboard"
    # CHART = "chart"
    # FLOWCHART = "flowchart"
    # INFOGRAPHIC = "infographic"
    # TABLE = "table"
    # MAP = "map"
    # HEATMAP = "heatmap"
    # BLUEPRINT = "blueprint"
    # HANDWRITTEN_NOTE = "handwritten_note"
    # LOGO = "logo"
    # TEXT_DOCUMENT = "text_document"
    # SCREENSHOT = "screenshot"
    # ARCHITECTURAL_PLAN = "architectural_plan"
    # X_RAY = "x_ray"
    # MEDICAL_IMAGE = "medical_image"
    # SATELLITE_IMAGE = "satellite_image"
    # ICON = "icon"
    # ANIMATION_FRAME = "animation_frame"
    # TIMELINE = "timeline"
    # ORGANIZATIONAL_CHART = "organizational_chart"
    # NETWORK_DIAGRAM = "network_diagram"
    # HISTOGRAM = "histogram"
    # VECTOR_GRAPHIC = "vector_graphic"
    # COMIC = "comic"
    # TECHNICAL_DRAWING = "technical_drawing"

    def display_name(self) -> str:
        return snake_to_capitalize_first_letter(self.value)


class ImageClassification(StructuredContent):
    description: str = Field(json_schema_extra={ExtraFieldAttribute.IS_HIDDEN: True})
    category: ImageCategory
    theme: str
