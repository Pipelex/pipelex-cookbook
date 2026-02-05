"""
PipeFunc implementations for expense validation rules.

These functions implement deterministic business rules for expense validation.
"""

from pipelex.core.memory.working_memory import WorkingMemory
from pipelex.core.stuffs.list_content import ListContent
from pipelex.system.registries.func_registry import pipe_func

from examples.wip.validate_expense_data.data import SPENDING_LIMITS
from examples.wip.validate_expense_data.structures.expense_validator__expense_report import ExpenseReport
from examples.wip.validate_expense_data.structures.expense_validator__expense_with_receipt import ExpenseWithReceipt
from examples.wip.validate_expense_data.structures.expense_validator__spending_limit_check import SpendingLimitCheck
from examples.wip.validate_expense_data.structures.expense_validator__weekend_check import WeekendCheck

# ============================================================================
# PIPEFUNC IMPLEMENTATIONS
# ============================================================================


@pipe_func("extract_expenses_list")
async def extract_expenses_list(working_memory: WorkingMemory) -> ListContent[ExpenseWithReceipt]:
    """
    Extracts the expenses list from an ExpenseReport for batch processing.
    Returns a list of ExpenseWithReceipt items.
    """
    report = working_memory.get_stuff_as("report", ExpenseReport)
    return ListContent(items=report.expenses_with_receipts)


@pipe_func("check_spending_limit")
async def check_spending_limit(working_memory: WorkingMemory) -> SpendingLimitCheck:
    """
    Checks if expense amount is within spending limits for employee seniority and category.

    Rules:
    - Each seniority level has specific limits per expense category
    - Higher seniority = higher limits
    - Amount exceeding limit results in rejection
    """

    report = working_memory.get_stuff_as("report", ExpenseReport)
    expense_with_receipt = working_memory.get_stuff_as("expense_with_receipt", ExpenseWithReceipt)

    # Get the limit for this seniority and category
    seniority_limits = SPENDING_LIMITS.get(report.employee.seniority, SPENDING_LIMITS["Junior"])
    limit_amount = seniority_limits.get(expense_with_receipt.expense.category, 100.0)

    within_limit = expense_with_receipt.expense.total_amount <= limit_amount
    exceeded_by = max(0.0, expense_with_receipt.expense.total_amount - limit_amount)

    return SpendingLimitCheck(
        within_limit=within_limit,
        limit_amount=limit_amount,
        exceeded_by=exceeded_by,
        category=expense_with_receipt.expense.category,
        seniority=report.employee.seniority,
    )


@pipe_func("check_weekend")
async def check_weekend(working_memory: WorkingMemory) -> WeekendCheck:
    """
    Checks if expense occurred on a weekend (not allowed per policy).

    Rules:
    - Expenses on Saturday or Sunday require prior manager approval
    - Weekday expenses are automatically valid for this check
    """

    expense_with_receipt = working_memory.get_stuff_as("expense_with_receipt", ExpenseWithReceipt)

    # Handle if expense_date is a string
    day_of_week = expense_with_receipt.expense.expense_date.strftime("%A")
    is_weekday = expense_with_receipt.expense.expense_date.weekday() < 5  # Monday=0, Sunday=6

    if is_weekday:
        message = "Expense on valid business day"
    else:
        message = "Weekend expenses require prior manager approval"

    return WeekendCheck(
        is_weekday=is_weekday,
        day_of_week=day_of_week,
        message=message,
    )
