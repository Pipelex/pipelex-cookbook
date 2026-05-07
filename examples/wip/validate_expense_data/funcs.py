from __future__ import annotations

from datetime import date

from pipelex.core.memory.working_memory import WorkingMemory
from pipelex.core.stuffs.list_content import ListContent
from pipelex.system.registries.func_registry import pipe_func

from examples.wip.validate_expense_data.data import SPENDING_LIMITS
from examples.wip.validate_expense_data.structures.expense_validator__expense import expense_validator__Expense
from examples.wip.validate_expense_data.structures.expense_validator__expense_report import expense_validator__ExpenseReport
from examples.wip.validate_expense_data.structures.expense_validator__expense_validation_result import expense_validator__ExpenseValidationResult
from examples.wip.validate_expense_data.structures.expense_validator__purpose_quality_check import expense_validator__PurposeQualityCheck
from examples.wip.validate_expense_data.structures.expense_validator__reasonable_amount_check import expense_validator__ReasonableAmountCheck
from examples.wip.validate_expense_data.structures.expense_validator__receipt_match_check import expense_validator__ReceiptMatchCheck
from examples.wip.validate_expense_data.structures.expense_validator__spending_limit_check import expense_validator__SpendingLimitCheck
from examples.wip.validate_expense_data.structures.expense_validator__timelines_check import expense_validator__TimelinesCheck
from examples.wip.validate_expense_data.structures.expense_validator__validation_report import expense_validator__ValidationReport
from examples.wip.validate_expense_data.structures.expense_validator__weekend_check import expense_validator__WeekendCheck

# Maximum days allowed for expense submission (company policy)
SUBMISSION_DEADLINE_DAYS = 30

# Grace period for late submissions (warning only)
LATE_GRACE_PERIOD_DAYS = 45


# ============================================================================
# PIPEFUNC IMPLEMENTATIONS
# ============================================================================


@pipe_func("extract_expenses_list")
async def extract_expenses_list(working_memory: WorkingMemory) -> ListContent[expense_validator__Expense]:
    """
    Extracts the expenses list from the parsed expense report.
    """
    report = working_memory.get_stuff_as("report", expense_validator__ExpenseReport)
    return ListContent(items=report.expenses)


@pipe_func("check_spending_limit")
async def check_spending_limit(working_memory: WorkingMemory) -> expense_validator__SpendingLimitCheck:
    """
    Checks if expense amount is within spending limits for employee seniority and category.

    Rules:
    - Each seniority level has specific limits per expense category
    - Higher seniority = higher limits
    - Amount exceeding limit results in rejection or cap
    """
    report = working_memory.get_stuff_as("report", expense_validator__ExpenseReport)
    expense = working_memory.get_stuff_as("expense", expense_validator__Expense)

    # Get the limit for this seniority and category
    seniority_limits = SPENDING_LIMITS.get(report.employee.seniority, SPENDING_LIMITS["Junior"])
    limit_amount = seniority_limits.get(expense.category, 100.0)

    within_limit = expense.total_amount <= limit_amount
    exceeded_by = max(0.0, expense.total_amount - limit_amount)

    return expense_validator__SpendingLimitCheck(
        expense_id=expense.expense_id,
        within_limit=within_limit,
        limit_amount=limit_amount,
        claimed_amount=expense.total_amount,
        exceeded_by=exceeded_by,
        category=expense.category,
        seniority=report.employee.seniority,
    )


@pipe_func("check_weekend")
async def check_weekend(working_memory: WorkingMemory) -> expense_validator__WeekendCheck:
    """
    Checks if expense occurred on a weekend.

    Policy:
    - Weekday expenses: compliant
    - Weekend expenses: requires prior manager approval
    - Travel/accommodation on weekends may be acceptable if part of business trip
    """

    expense = working_memory.get_stuff_as("expense", expense_validator__Expense)

    day_of_week = expense.expense_date.strftime("%A")
    weekday_num = expense.expense_date.weekday()
    is_weekday = weekday_num < 5  # Monday=0, Sunday=6

    if is_weekday:
        policy_status = "compliant"
        message = f"expense_validator__Expense on {day_of_week} - valid business day"
    else:
        # Check if category might be acceptable on weekends
        if expense.category in ["travel", "accommodation"]:
            policy_status = "requires_approval"
            message = f"Weekend {expense.category} expense on {day_of_week} - may be acceptable for business trips, requires manager confirmation"
        else:
            policy_status = "requires_approval"
            message = f"Weekend expense on {day_of_week} - requires prior manager approval per company policy"

    return expense_validator__WeekendCheck(
        expense_id=expense.expense_id,
        is_weekday=is_weekday,
        day_of_week=day_of_week,
        policy_status=policy_status,
        message=message,
    )


@pipe_func("check_timeliness")
async def check_timeliness(working_memory: WorkingMemory) -> expense_validator__TimelinesCheck:
    """
    Checks if expense was submitted within the allowed timeframe.

    Policy:
    - Expenses must be submitted within 30 days of the expense date
    - Grace period of 45 days with warning
    - Beyond 45 days: rejected as too late
    """
    expense = working_memory.get_stuff_as("expense", expense_validator__Expense)

    # Calculate days since expense
    today = date.today()
    # expense_date may be datetime or date, normalize to date
    expense_date = expense.expense_date.date() if hasattr(expense.expense_date, "date") else expense.expense_date
    days_since = (today - expense_date).days

    if days_since <= SUBMISSION_DEADLINE_DAYS:
        is_timely = True
        policy_status = "compliant"
        message = f"Submitted within {SUBMISSION_DEADLINE_DAYS}-day policy window ({days_since} days since expense)"
    elif days_since <= LATE_GRACE_PERIOD_DAYS:
        is_timely = True
        policy_status = "late_but_acceptable"
        message = f"Submitted {days_since} days after expense - past {SUBMISSION_DEADLINE_DAYS}-day \
            deadline but within {LATE_GRACE_PERIOD_DAYS}-day grace period"
    else:
        is_timely = False
        policy_status = "too_late"
        message = f"Submitted {days_since} days after expense - exceeds {LATE_GRACE_PERIOD_DAYS}-day \
            maximum, may require special approval"

    return expense_validator__TimelinesCheck(
        expense_id=expense.expense_id,
        is_timely=is_timely,
        days_since_expense=days_since,
        submission_deadline=SUBMISSION_DEADLINE_DAYS,
        policy_status=policy_status,
        message=message,
    )


@pipe_func("compose_expense_result")
async def compose_expense_result(working_memory: WorkingMemory) -> expense_validator__ExpenseValidationResult:
    """
    Composes the final validation result for a single expense based on all checks.

    Approval logic:
    - Receipt required and must match (critical)
    - Must be within spending limit (critical)
    - Weekend expenses need approval (warning unless policy violation)
    - Timeliness check (critical if too late)
    - Purpose quality (warning or requires clarification)
    - Reasonable amount (warning only)
    """
    expense = working_memory.get_stuff_as("expense", expense_validator__Expense)
    receipt_check = working_memory.get_stuff_as("receipt_check", expense_validator__ReceiptMatchCheck)
    limit_check = working_memory.get_stuff_as("limit_check", expense_validator__SpendingLimitCheck)
    weekend_check = working_memory.get_stuff_as("weekend_check", expense_validator__WeekendCheck)
    timeliness_check = working_memory.get_stuff_as("timeliness_check", expense_validator__TimelinesCheck)
    purpose_check = working_memory.get_stuff_as("purpose_check", expense_validator__PurposeQualityCheck)
    reasonable_check = working_memory.get_stuff_as("reasonable_check", expense_validator__ReasonableAmountCheck)

    rejection_reasons: list[str] = []
    warnings: list[str] = []
    pending_clarification = False
    action_items: list[str] = []

    # === CRITICAL CHECKS (cause rejection) ===

    # Receipt check
    if not receipt_check.has_receipt:
        rejection_reasons.append("No receipt provided - all expenses require supporting documentation")
        action_items.append("Submit receipt for this expense")
    elif not receipt_check.is_matching:
        discrepancy_details = receipt_check.discrepancies or "Receipt does not match expense details"
        rejection_reasons.append(f"Receipt verification failed: {discrepancy_details}")
        action_items.append("Provide correct receipt or amend expense details")

    # Spending limit check
    if not limit_check.within_limit:
        rejection_reasons.append(
            f"Exceeds {limit_check.seniority}-level spending limit for {limit_check.category} "
            f"(limit: ${limit_check.limit_amount:.2f}, exceeded by: ${limit_check.exceeded_by:.2f})"
        )
        action_items.append("Request limit exception from department head or split expense")

    # Timeliness check
    if not timeliness_check.is_timely:
        rejection_reasons.append(
            f"Submission too late: {timeliness_check.days_since_expense} days since expense (maximum: {LATE_GRACE_PERIOD_DAYS} days)"
        )
        action_items.append("Request late submission exception from finance")
    elif timeliness_check.policy_status == "late_but_acceptable":
        warnings.append(timeliness_check.message)

    # Purpose quality check
    if purpose_check.recommendation == "reject":
        rejection_reasons.append(f"Business purpose inadequate: {purpose_check.assessment}")
        action_items.append("Provide detailed business justification")
    elif purpose_check.recommendation == "request_clarification":
        pending_clarification = True
        warnings.append(f"Purpose needs clarification: {purpose_check.assessment}")
        action_items.append("Provide additional details about business purpose")
    elif purpose_check.recommendation == "approve_with_note":
        warnings.append(f"Purpose acceptable but could be improved: {purpose_check.assessment}")

    # === WARNING CHECKS (don't prevent approval) ===

    # Weekend check
    if weekend_check.policy_status == "requires_approval":
        warnings.append(weekend_check.message)
        action_items.append("Obtain manager approval for weekend expense")

    # Reasonable amount check
    if not reasonable_check.is_reasonable:
        variance_msg = f"Amount ${expense.total_amount:.2f} flagged as {reasonable_check.variance_category}"
        warnings.append(f"{variance_msg}: {reasonable_check.assessment}")
    elif reasonable_check.variance_category in ["slightly_high", "significantly_high"]:
        warnings.append(
            f"Amount above typical range (${reasonable_check.expected_range_min:.0f}-${reasonable_check.expected_range_max:.0f}): "
            f"{reasonable_check.assessment}"
        )

    # Low confidence receipt
    if receipt_check.has_receipt and receipt_check.confidence == "low":
        warnings.append("Receipt quality is poor - recommend keeping original for audit purposes")

    # === DETERMINE FINAL STATUS ===

    claimed_amount = expense.total_amount

    if rejection_reasons:
        is_approved = False
        approval_status = "rejected"
        approved_amount = 0.0
    elif pending_clarification:
        is_approved = False
        approval_status = "pending_clarification"
        approved_amount = 0.0  # Pending until clarification received
    elif warnings:
        is_approved = True
        approval_status = "approved_with_warnings"
        approved_amount = claimed_amount
    else:
        is_approved = True
        approval_status = "approved"
        approved_amount = claimed_amount

    # Compile action required
    action_required = "; ".join(action_items) if action_items else "None"

    # Use extracted merchant from receipt if expense merchant is unknown
    merchant = expense.merchant
    if merchant == "<UNKNOWN>" and receipt_check.has_receipt:
        merchant = receipt_check.extracted_merchant

    return expense_validator__ExpenseValidationResult(
        expense_id=expense.expense_id,
        expense_category=expense.category,
        expense_merchant=merchant,
        is_approved=is_approved,
        approval_status=approval_status,
        claimed_amount=claimed_amount,
        approved_amount=approved_amount,
        rejection_reasons=rejection_reasons,
        warnings=warnings,
        action_required=action_required,
    )


@pipe_func("compose_validation_report")
async def compose_validation_report(working_memory: WorkingMemory) -> expense_validator__ValidationReport:
    """
    Composes the final validation report with summary statistics and executive notes.
    """
    report = working_memory.get_stuff_as("report", expense_validator__ExpenseReport)
    validations_stuff = working_memory.get_stuff_as_list("expense_validations", expense_validator__ExpenseValidationResult)

    # Calculate summary statistics
    total_claimed = sum(r.claimed_amount for r in validations_stuff.items)
    total_approved = sum(r.approved_amount for r in validations_stuff.items if r.approval_status in ["approved", "approved_with_warnings"])
    total_pending = sum(r.claimed_amount for r in validations_stuff.items if r.approval_status == "pending_clarification")
    total_rejected = total_claimed - total_approved - total_pending

    num_expenses = len(validations_stuff.items)
    expenses_approved = sum(1 for r in validations_stuff.items if r.approval_status in ["approved", "approved_with_warnings"])
    expenses_rejected = sum(1 for r in validations_stuff.items if r.approval_status == "rejected")
    expenses_pending = sum(1 for r in validations_stuff.items if r.approval_status == "pending_clarification")

    approval_rate = (expenses_approved / num_expenses * 100) if num_expenses > 0 else 0.0

    # Generate executive summary notes
    summary_parts: list[str] = []

    summary_parts.append(
        f"expense_validator__Expense report for {report.employee.full_name} ({report.employee.seniority} - {report.employee.department})"
    )
    summary_parts.append(f"Total: {num_expenses} expenses, ${total_claimed:.2f} claimed")

    if expenses_approved > 0:
        summary_parts.append(f"Approved: {expenses_approved} expenses (${total_approved:.2f})")

    if expenses_pending > 0:
        summary_parts.append(f"Pending clarification: {expenses_pending} expenses (${total_pending:.2f})")

    if expenses_rejected > 0:
        summary_parts.append(f"Rejected: {expenses_rejected} expenses (${total_rejected:.2f})")

    # Note any patterns of concern
    warning_count = sum(len(r.warnings or []) for r in validations_stuff.items)
    if warning_count > 3:
        summary_parts.append(f"Note: {warning_count} warnings flagged across expenses - recommend review with employee")

    # Check for missing receipts pattern
    missing_receipts = sum(1 for r in validations_stuff.items if "No receipt" in str(r.rejection_reasons))
    if missing_receipts > 1:
        summary_parts.append(f"Attention: {missing_receipts} expenses missing receipts - remind employee of documentation requirements")

    summary_notes = ". ".join(summary_parts) + "."

    return expense_validator__ValidationReport(
        employee=report.employee,
        expense_results=validations_stuff.items,
        total_claimed=total_claimed,
        total_approved=total_approved,
        total_rejected=total_rejected,
        total_pending=total_pending,
        approval_rate=approval_rate,
        expenses_approved=expenses_approved,
        expenses_rejected=expenses_rejected,
        expenses_pending=expenses_pending,
        summary_notes=summary_notes,
    )
