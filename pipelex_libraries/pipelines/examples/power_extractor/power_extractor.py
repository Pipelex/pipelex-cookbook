from datetime import date, datetime
from enum import StrEnum
from typing import List, Optional

from pipelex.core.stuff_content import ImageContent, PageContent, StructuredContent, TextAndImagesContent, TextContent
from pipelex.core.working_memory import WorkingMemory
from pydantic import BaseModel


class PageContentAndMarkdownMatchError(ValueError):
    pass


class IndicePerformanceEnergetique(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class IndiceEmissions(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class Dpe(StructuredContent):
    address: Optional[str] = None
    date_of_issue: Optional[datetime] = None
    date_of_expiration: Optional[datetime] = None
    energy_efficiency_class: Optional[IndicePerformanceEnergetique] = None
    per_year_per_m2_consumption: Optional[float] = None
    co2_emission_class: Optional[IndiceEmissions] = None
    per_year_per_m2_co2_emissions: Optional[float] = None
    yearly_energy_costs: Optional[float] = None


class Products(StructuredContent):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class ProofOfPurchase(StructuredContent):
    date_of_purchase: Optional[datetime] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    purchase_number: Optional[str] = None
    products: Optional[List[Products]] = None


# TODO: wrap this in a PipeFunc
def merge_markdown_and_images(working_memory: WorkingMemory) -> TextAndImagesContent:
    # Pages extracted from the PDF by PipeOCR
    page_contents_list = working_memory.get_stuff_as_list(item_type=PageContent, name="page_contents")
    # Markdown text extracted from the Pages by PipeLLM
    page_markdown_list = working_memory.get_stuff_as_list(item_type=TextContent, name="markdowns")

    # Check if the number of markdown and text_and_images are the same
    if len(page_markdown_list.items) != len(page_contents_list.items):
        raise PageContentAndMarkdownMatchError(
            f"The number of markdown and page_contents items are not the same: {len(page_markdown_list.items)} != {len(page_contents_list.items)}"
        )

    # Concatenate the markdown text
    concatenated_markdown_text: str = "\n".join([page_markdown.text for page_markdown in page_markdown_list.items])

    # Aggregate the images from the page contents
    image_contents: List[ImageContent] = []
    for page_content in page_contents_list.items:
        if page_content.text_and_images.images:
            image_contents.extend(page_content.text_and_images.images)

    return TextAndImagesContent(
        text=TextContent(text=concatenated_markdown_text),
        images=image_contents,
    )
