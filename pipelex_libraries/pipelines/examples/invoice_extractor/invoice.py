from datetime import datetime
from typing import List, Literal, Optional

from pipelex.core.stuff_content import StructuredContent
from pipelex.types import StrEnum
from pydantic import Field, field_validator


class InvoiceCategory(StrEnum):
    BILL = "bill"
    RECEIPT = "receipt"


class InvoiceDetails(StructuredContent):
    """Classification of the invoice type (formal bill vs simple receipt)"""

    category: Optional[Literal[InvoiceCategory.BILL, InvoiceCategory.RECEIPT]] = None
    explanation: Optional[str] = None


class Invoice(StructuredContent):
    """Invoice information extracted from text, supporting both formal bills and receipts"""

    invoice_id: Optional[str] = Field(None, description="Unique identifier for the invoice")
    invoice_number: Optional[str] = Field(None, description="Invoice number as shown on the document")
    date: Optional[datetime] = Field(None, description="Date when the invoice was issued")
    time: Optional[str] = Field(None, description="Time of the transaction if available")

    amount_incl_tax: Optional[float] = Field(None, description="Total amount including taxes")
    amount_excl_tax: Optional[float] = Field(None, description="Net amount excluding taxes")
    vat_amount: Optional[float] = Field(None, description="Total VAT/tax amount")
    vat_rates: Optional[List[float]] = Field(None, description="List of VAT rates applied")

    vendor: Optional[str] = Field(None, description="Name of the vendor/seller")
    vendor_address: Optional[str] = Field(None, description="Complete address of the vendor")
    vendor_siret: Optional[str] = Field(None, description="SIRET number of the vendor (French company registration)")
    vendor_vat_number: Optional[str] = Field(None, description="VAT registration number of the vendor")

    company_name: Optional[str] = Field(None, description="Name of the purchasing company")
    company_address: Optional[str] = Field(None, description="Address of the purchasing company")

    description: Optional[str] = Field(None, description="Description of goods or services purchased")
    category: Optional[InvoiceDetails] = Field(None, description="Category or type of expense")
    text: Optional[str] = Field(None, description="Raw text extracted from the invoice")

    @field_validator("date")
    @classmethod
    def remove_tzinfo(cls, date: Optional[datetime]) -> Optional[datetime]:
        if date is not None:
            return date.replace(tzinfo=None)
        return date
