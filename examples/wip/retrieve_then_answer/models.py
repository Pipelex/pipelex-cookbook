from typing import Any, Generic, List, Literal, Optional, TypeVar, Union

from pipelex.core.stuffs.structured_content import StructuredContent
from pipelex.types import StrEnum
from pydantic import Field, model_validator
from typing_extensions import Self, override

T = TypeVar("T")


class BaseAnswer(StrEnum):
    NOT_APPLICABLE = "Not applicable"
    INDETERMINATE = "Indeterminate"


# TODO: we should make this system easy to apply using a simple parameter on a chosen structure
class SourcedAnswer(StructuredContent, Generic[T]):
    """
    This model represents an answer to a question given a excerpt of a text.
    Add a short comment explaining how you determined the answer.

    Make sure you return citations (taken from the text) in an array if you can answer the question.
    Do not force a citation if you cannot answer the question.
    """

    answer: Union[T, Literal[BaseAnswer.NOT_APPLICABLE, BaseAnswer.INDETERMINATE]] = Field(description="The answer to the question")
    short_comment: str = Field(..., description="A short comment explaining how you determined the answer.")
    citations: Optional[List[str]] = Field(default=None, description="The array of citations that contains the answer.")

    @property
    def indeterminate(self) -> bool:
        return self.answer == BaseAnswer.INDETERMINATE

    @property
    def not_applicable(self) -> bool:
        return self.answer == BaseAnswer.NOT_APPLICABLE

    @model_validator(mode="after")
    def validate_answer(self) -> Self:
        if not self.answer:
            raise ValueError("Answer must be provided")

        if not (self.indeterminate or self.answer) and not self.citations:
            raise ValueError("Citations must be provided when answer is not 'Indeterminate'")

        return self

    @override
    def render_spreadsheet(self) -> str:
        return str(self.answer)


class Fees(SourcedAnswer[Any]):
    class Value(StrEnum):
        PERCENTAGE = "Percentage"
        AMOUNT = "Amount"
        INDETERMINATE = "Indeterminate"

    class Currency(StrEnum):
        USD = "USD"
        EUR = "EUR"
        GBP = "GBP"
        AUD = "AUD"
        CAD = "CAD"
        UNKNOWN = "Unknown currency"

    answer: Union[float, BaseAnswer] = Field(
        default=BaseAnswer.INDETERMINATE,
        description="The fee value - for percentages use decimal (e.g. 2.5 for 2.5%), for amounts use the absolute value",
    )
    fee_type: Value = Field(default=Value.PERCENTAGE, description="The type of fee (percentage or amount)")
    fee_currency: Optional[Currency] = Field(
        default=None, description="The currency of the fee amount. Required when fee_type is AMOUNT, should be None for PERCENTAGE"
    )

    @model_validator(mode="after")
    def validate_fee(self) -> Self:
        if isinstance(self.answer, float):
            if self.answer < 0 or self.answer > 100:
                raise ValueError("Fee value must be between 0 and 100")
            if self.fee_type == self.Value.AMOUNT and not self.fee_currency:
                raise ValueError("Currency is required when fee type is AMOUNT")
            if self.fee_type == self.Value.PERCENTAGE and self.fee_currency:
                raise ValueError("Currency should not be set when fee type is PERCENTAGE")
        return self

    @override
    def render_spreadsheet(self) -> str:
        if self.not_applicable:
            return BaseAnswer.NOT_APPLICABLE.value
        elif self.indeterminate:
            return BaseAnswer.INDETERMINATE.value
        if self.fee_type == self.Value.PERCENTAGE:
            return f"{self.answer}"
        else:
            return f"{self.answer} {self.fee_currency.value if self.fee_currency else 'Unknown'}"
