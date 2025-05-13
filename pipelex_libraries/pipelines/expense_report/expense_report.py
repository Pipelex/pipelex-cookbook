# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

from datetime import datetime
from enum import StrEnum
from typing import List, Literal, Optional

from pipelex.core.stuff_content import StructuredContent
from pydantic import Field, ValidationInfo, field_validator


class Employee(StructuredContent):
    """Employee information for expense tracking"""

    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[str] = None


#########################################################
#####################  Invoice  ########################
#########################################################


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


#########################################################
#####################  Expense  ########################
#########################################################
class ExpenseCategoryEnum(StrEnum):
    RESTAURATION = "restauration"
    MILEAGE = "mileage"
    TRIP = "trip"
    OFFICE_SUPPLIES = "office_supplies"


class ExpenseCategory(StructuredContent):
    """Type of expense (restauration, péage, billet d'avion, accessoires d'ordinateurs, affaires de bureau)"""

    category: Optional[
        Literal[
            ExpenseCategoryEnum.RESTAURATION,
            ExpenseCategoryEnum.MILEAGE,
            ExpenseCategoryEnum.TRIP,
            ExpenseCategoryEnum.OFFICE_SUPPLIES,
        ]
    ] = None
    explanation: Optional[str] = None


class Expense(StructuredContent):
    """A single expense line item/article"""

    date: Optional[datetime] = None
    amount_incl_tax: Optional[float] = None
    amount_excl_tax: Optional[float] = None
    description: Optional[str] = None
    category: Optional[ExpenseCategory] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    invoice: Optional[Invoice] = None


class ExpenseReport(StructuredContent):
    """Expense report information extracted from text"""

    report_date: Optional[datetime] = None
    employee: Optional[Employee] = None
    expenses: Optional[List[Expense]] = None
    purpose: Optional[str] = None


class ExpenseValidationEnum(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"


class ExpenseValidation(StructuredContent):
    """
    Validation result for an expense
        - "valid" if all rules are met
        - "invalid" if any rules are violated
        - "needs_review" if some information is missing
    """

    status: Optional[Literal[ExpenseValidationEnum.VALID, ExpenseValidationEnum.INVALID, ExpenseValidationEnum.NEEDS_REVIEW]] = None
    issues: Optional[List[str]] = Field(default=None, description="Include specific issues in the issues list if any rules are not met.")
    reason: Optional[str] = None

    @field_validator("issues")
    @classmethod
    def validate_issues_for_valid_status(cls, issues: Optional[List[str]], info: ValidationInfo) -> Optional[List[str]]:
        if info.data.get("status") == ExpenseValidationEnum.VALID and issues is not None:
            raise ValueError("Issues must be None when status is 'valid'")
        return issues


class ExpenseValidationCombo(StructuredContent):
    """Combined validation result for an expense"""

    urssaf_validation: Optional[ExpenseValidation] = None
    custom_validation: Optional[ExpenseValidation] = None


class VAT(StructuredContent):
    """Value Added Tax information for expenses"""

    vat_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_type: Optional[str] = None
    explanation: Optional[str] = None


class TripLocationCategoryEnum(StrEnum):
    METROPOLITAN = "metropolitan"
    OVERSEAS = "overseas"


class TripCategory(StructuredContent):
    """Model to represent the type of trip (domestic or international)"""

    category: Literal[TripLocationCategoryEnum.METROPOLITAN, TripLocationCategoryEnum.OVERSEAS] = Field(
        description="Category of location for the trip"
    )
