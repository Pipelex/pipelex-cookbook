"""
PipeFunc implementations for expense validation rules.

These functions implement deterministic business rules for expense validation.
"""

from datetime import datetime

from pipelex.core.memory.working_memory import WorkingMemory
from pipelex.core.stuffs.list_content import ListContent
from pipelex.core.stuffs.stuff_content import StuffContent
from examples.c_advanced.gen_expense_data.data import SPENDING_LIMITS
from pipelex.system.registries.func_registry import pipe_func

# ============================================================================
# PIPEFUNC IMPLEMENTATIONS
# ============================================================================


@pipe_func("extract_expenses_list")
async def extract_expenses_list(working_memory: WorkingMemory) -> ListContent:  # type: ignore
    """
    Extracts the expenses list from an ExpenseReport for batch processing.
    Returns a list of ExpenseWithReceipt items.
    """
    report_stuff = working_memory.get_stuff("report")
    report = report_stuff.content
    return ListContent(items=report.expenses_with_receipts)  # type: ignore


@pipe_func("check_receipt_presence")
async def check_receipt_presence(working_memory: WorkingMemory) -> StuffContent:
    """
    Checks if a receipt image is present for the expense.

    Rules:
    - Every expense must have a receipt attached
    - Missing receipt = automatic rejection
    """
    # Import here to avoid circular imports
    from examples.c_advanced.gen_expense_data.structures.expense_validator__receipt_presence_check import ReceiptPresenceCheck

    expense_stuff = working_memory.get_stuff("expense_with_receipt")
    expense_with_receipt = expense_stuff.content

    receipt_image = getattr(expense_with_receipt, "receipt_image", None)
    has_receipt = receipt_image is not None

    return ReceiptPresenceCheck(
        has_receipt=has_receipt,
        message="Receipt image attached" if has_receipt else "No receipt image found - receipt required for reimbursement",
    )


@pipe_func("check_spending_limit")
async def check_spending_limit(working_memory: WorkingMemory) -> StuffContent:
    """
    Checks if expense amount is within spending limits for employee seniority and category.

    Rules:
    - Each seniority level has specific limits per expense category
    - Higher seniority = higher limits
    - Amount exceeding limit results in rejection
    """
    from examples.c_advanced.gen_expense_data.structures.expense_validator__spending_limit_check import SpendingLimitCheck

    report_stuff = working_memory.get_stuff("report")
    expense_stuff = working_memory.get_stuff("expense_with_receipt")

    report = report_stuff.content
    expense_with_receipt = expense_stuff.content

    seniority: str = report.employee.seniority  # type: ignore
    category: str = expense_with_receipt.expense.category  # type: ignore
    amount: float = expense_with_receipt.expense.total_amount  # type: ignore

    # Get the limit for this seniority and category
    seniority_limits = SPENDING_LIMITS.get(seniority, SPENDING_LIMITS["Junior"])
    limit_amount = seniority_limits.get(category, 100.0)

    within_limit = amount <= limit_amount
    exceeded_by = max(0.0, amount - limit_amount)

    return SpendingLimitCheck(
        within_limit=within_limit,
        limit_amount=limit_amount,
        exceeded_by=exceeded_by,
        category=category,
        seniority=seniority,
    )


@pipe_func("check_weekend")
async def check_weekend(working_memory: WorkingMemory) -> StuffContent:
    """
    Checks if expense occurred on a weekend (not allowed per policy).

    Rules:
    - Expenses on Saturday or Sunday require prior manager approval
    - Weekday expenses are automatically valid for this check
    """
    from examples.c_advanced.gen_expense_data.structures.expense_validator__weekend_check import WeekendCheck

    expense_stuff = working_memory.get_stuff("expense_with_receipt")
    expense_with_receipt = expense_stuff.content

    expense_date = expense_with_receipt.expense.expense_date  # type: ignore

    # Handle if expense_date is a string
    if isinstance(expense_date, str):
        expense_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
    elif isinstance(expense_date, datetime):
        expense_date = expense_date.date()

    day_of_week = expense_date.strftime("%A")
    is_weekday = expense_date.weekday() < 5  # Monday=0, Sunday=6

    if is_weekday:
        message = "Expense on valid business day"
    else:
        message = "Weekend expenses require prior manager approval"

    return WeekendCheck(
        is_weekday=is_weekday,
        day_of_week=day_of_week,
        message=message,
    )
