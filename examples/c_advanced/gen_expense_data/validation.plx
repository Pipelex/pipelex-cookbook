domain = "expense_validator"
description = "Validates expense reports against company rules and determines reimbursement eligibility"
main_pipe = "validate_expense_report"

# ============================================================================
# EXPENSE REPORT CONCEPTS (independent from generation domain)
# ============================================================================

[concept.Employee]
description = "Employee information from the expense report"

[concept.Employee.structure]
employee_id = { type = "text", description = "Unique employee identifier", required = true }
full_name = { type = "text", description = "Employee full name", required = true }
email = { type = "text", description = "Employee email address", required = true }
department = { type = "text", description = "Department name", required = true }
job_title = { type = "text", description = "Job title", required = true }
seniority = { type = "text", description = "Seniority level", choices = ["Junior", "Senior", "Lead", "Manager", "Director", "VP", "Executive"], required = true }

[concept.Expense]
description = "A single expense line item"

[concept.Expense.structure]
expense_id = { type = "text", description = "Unique expense identifier", required = true }
expense_date = { type = "date", description = "Date of the expense", required = true }
total_amount = { type = "number", description = "Total expense amount", required = true }
currency = { type = "text", description = "Currency code", required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.ExpenseWithReceipt]
description = "An expense paired with its receipt image"

[concept.ExpenseWithReceipt.structure]
expense = { type = "concept", concept_ref = "expense_validator.Expense", description = "The expense details", required = true }
receipt_image = { type = "concept", concept_ref = "Image", description = "The receipt image (null if missing)" }

[concept.ExpenseReport]
description = "Complete expense report extracted from PDF"

[concept.ExpenseReport.structure]
employee = { type = "concept", concept_ref = "expense_validator.Employee", description = "The employee", required = true }
expenses_with_receipts = { type = "list", item_type = "concept", item_concept_ref = "expense_validator.ExpenseWithReceipt", description = "List of expenses with receipts", required = true }

# ============================================================================
# VALIDATION CHECK RESULT CONCEPTS
# ============================================================================

[concept.ReceiptPresenceCheck]
description = "Check if a receipt is present for the expense"

[concept.ReceiptPresenceCheck.structure]
has_receipt = { type = "boolean", description = "Whether a receipt image is attached", required = true }
message = { type = "text", description = "Explanation", required = true }

[concept.ReceiptMatchCheck]
description = "LLM assessment of whether receipt matches the expense details"

[concept.ReceiptMatchCheck.structure]
is_matching = { type = "boolean", description = "Whether receipt matches expense", required = true }
merchant_matches = { type = "boolean", description = "Merchant name matches", required = true }
amount_matches = { type = "boolean", description = "Amount matches", required = true }
date_matches = { type = "boolean", description = "Date matches", required = true }
confidence = { type = "text", description = "Confidence level", choices = ["high", "medium", "low"], required = true }
discrepancies = { type = "text", description = "Description of any discrepancies found" }

[concept.SpendingLimitCheck]
description = "Check if expense is within spending limits for seniority level"

[concept.SpendingLimitCheck.structure]
within_limit = { type = "boolean", description = "Whether expense is within limit", required = true }
limit_amount = { type = "number", description = "The applicable spending limit", required = true }
exceeded_by = { type = "number", description = "Amount exceeded (0 if within limit)", required = true }
category = { type = "text", description = "Expense category", required = true }
seniority = { type = "text", description = "Employee seniority level", required = true }

[concept.WeekendCheck]
description = "Check if expense occurred on a weekend (not allowed)"

[concept.WeekendCheck.structure]
is_weekday = { type = "boolean", description = "True if expense is on a weekday", required = true }
day_of_week = { type = "text", description = "Day name (Monday, Tuesday, etc.)", required = true }
message = { type = "text", description = "Explanation", required = true }

[concept.DuplicateCheck]
description = "Check for potential duplicate expenses"

[concept.DuplicateCheck.structure]
is_duplicate = { type = "boolean", description = "Whether this appears to be a duplicate", required = true }
similar_expense_id = { type = "text", description = "ID of similar expense if found" }
similarity_reason = { type = "text", description = "Why it might be a duplicate" }

[concept.ReasonableAmountCheck]
description = "Check if expense amount is reasonable for the category"

[concept.ReasonableAmountCheck.structure]
is_reasonable = { type = "boolean", description = "Whether amount is reasonable", required = true }
expected_range = { type = "text", description = "Expected range for this category", required = true }
assessment = { type = "text", description = "Explanation of assessment", required = true }

[concept.ExpenseValidationResult]
description = "Complete validation result for a single expense"

[concept.ExpenseValidationResult.structure]
expense_id = { type = "text", description = "The expense ID", required = true }
is_approved = { type = "boolean", description = "Whether expense is approved", required = true }
total_amount = { type = "number", description = "Expense amount", required = true }
approved_amount = { type = "number", description = "Approved amount (0 if rejected)", required = true }
issues = { type = "list", item_type = "text", description = "List of validation issues found" }

# ============================================================================
# MAIN VALIDATION PIPELINE
# ============================================================================

[pipe.validate_expense_report]
type = "PipeSequence"
description = "Main pipeline that validates an expense report from a PDF document"
inputs = { document = "Document" }
output = "Text"
steps = [
    { pipe = "extract_document_content", result = "pages" },
    { pipe = "parse_expense_report", result = "report" },
    { pipe = "extract_expenses_list", result = "expenses" },
    { pipe = "validate_single_expense", batch_over = "expenses", batch_as = "expense_with_receipt", result = "expense_validations" },
    { pipe = "compose_final_report", result = "validation_report" },
]

[pipe.extract_document_content]
type = "PipeExtract"
description = "Extracts text and images from the expense report PDF"
inputs = { document = "Document" }
output = "Page[]"

[pipe.parse_expense_report]
type = "PipeLLM"
description = "Parses extracted pages into a structured ExpenseReport"
inputs = { pages = "Page[]" }
output = "ExpenseReport"
model = { model = "base-claude", temperature = 0.1 }
prompt = """
Parse this expense report document into a structured ExpenseReport.

@pages

INSTRUCTIONS:
1. Extract employee information from the header:
   - employee_id, full_name, email, department, job_title, seniority

2. For each expense row in the table, extract:
   - expense_id, expense_date, total_amount, currency, business_purpose

3. Match each expense with its receipt image:
   - Look at the images in the pages
   - Each receipt image should be matched to its corresponding expense
   - If an expense has no matching receipt image, set receipt_image to null

4. Return the complete ExpenseReport with employee and all expenses_with_receipts.

IMPORTANT: The receipt images are in the pages. Extract them and match them to the correct expense based on visual content or position.
"""

[pipe.extract_expenses_list]
type = "PipeFunc"
description = "Extracts the list of expenses from the report for batch processing"
inputs = { report = "ExpenseReport" }
output = "ExpenseWithReceipt[]"
function_name = "extract_expenses_list"

# ============================================================================
# SINGLE EXPENSE VALIDATION
# ============================================================================

[pipe.validate_single_expense]
type = "PipeSequence"
description = "Validates a single expense against all company rules"
inputs = { report = "ExpenseReport", expense_with_receipt = "ExpenseWithReceipt" }
output = "Text"
steps = [
    { pipe = "check_receipt_presence", result = "receipt_check" },
    { pipe = "check_receipt_match", result = "match_check" },
    { pipe = "check_spending_limit", result = "limit_check" },
    { pipe = "check_weekend", result = "weekend_check" },
    { pipe = "check_reasonable_amount", result = "reasonable_check" },
    { pipe = "compose_expense_validation", result = "validation_result" },
]

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

[pipe.check_receipt_presence]
type = "PipeFunc"
description = "Checks if a receipt image is present for the expense"
inputs = { expense_with_receipt = "ExpenseWithReceipt" }
output = "ReceiptPresenceCheck"
function_name = "check_receipt_presence"

[pipe.check_receipt_match]
type = "PipeLLM"
description = "Uses vision LLM to verify receipt matches expense details"
inputs = { expense_with_receipt = "ExpenseWithReceipt" }
output = "ReceiptMatchCheck"
model = { model = "base-claude", temperature = 0.1 }
prompt = """
Verify if this receipt matches the expense claim.

EXPENSE DETAILS:
- Expense ID: $expense_with_receipt.expense.expense_id
- Amount: $expense_with_receipt.expense.total_amount $expense_with_receipt.expense.currency
- Date: $expense_with_receipt.expense.expense_date
- Category: $expense_with_receipt.expense.category

RECEIPT IMAGE:
$expense_with_receipt.receipt_image

VERIFY:
1. Does the total amount on the receipt match $expense_with_receipt.expense.total_amount?
3. Does the date on the receipt match $expense_with_receipt.expense.expense_date?

If no receipt image is provided, set is_matching=false and note "No receipt provided" in discrepancies.

Provide your assessment with confidence level.
"""

[pipe.check_spending_limit]
type = "PipeFunc"
description = "Checks if expense is within spending limits based on seniority and category"
inputs = { report = "ExpenseReport", expense_with_receipt = "ExpenseWithReceipt" }
output = "SpendingLimitCheck"
function_name = "check_spending_limit"

[pipe.check_weekend]
type = "PipeFunc"
description = "Checks if expense occurred on a weekend (not allowed per policy)"
inputs = { expense_with_receipt = "ExpenseWithReceipt" }
output = "WeekendCheck"
function_name = "check_weekend"

[pipe.check_reasonable_amount]
type = "PipeLLM"
description = "Assesses if expense amount is reasonable for the category"
inputs = { expense_with_receipt = "ExpenseWithReceipt" }
output = "ReasonableAmountCheck"
model = { model = "base-claude", temperature = 0.2 }
system_prompt = """
You are an expense auditor. Assess if expense amounts are reasonable based on typical business costs.

Typical ranges by category:
- Meals: $10-100 (individual), $50-500 (team/client)
- Travel (flights): $200-2000 depending on distance
- Accommodation: $100-400 per night
- Equipment: $50-2000 depending on item
- Supplies: $10-200
- Transportation: $20-200 (taxi/rideshare), $50-500 (car rental)
"""
prompt = """
Assess if this expense amount is reasonable:

Amount: $expense_with_receipt.expense.total_amount $expense_with_receipt.expense.currency
Business Purpose: $expense_with_receipt.expense.business_purpose

Is this amount reasonable for the stated category and purpose?
Provide the expected range and your assessment.
"""

# ============================================================================
# COMPOSITION PIPES
# ============================================================================

[pipe.compose_expense_validation]
type = "PipeCompose"
description = "Composes the validation result for a single expense"
inputs = { expense_with_receipt = "ExpenseWithReceipt", receipt_check = "ReceiptPresenceCheck", match_check = "ReceiptMatchCheck", limit_check = "SpendingLimitCheck", weekend_check = "WeekendCheck", reasonable_check = "ReasonableAmountCheck" }
output = "Text"

[pipe.compose_expense_validation.template]
category = "markdown"
template = """
## Expense: $expense_with_receipt.expense.expense_id

**Amount:** $expense_with_receipt.expense.total_amount $expense_with_receipt.expense.currency
**Date:** $expense_with_receipt.expense.expense_date
**Category:** $expense_with_receipt.expense.category
**Purpose:** $expense_with_receipt.expense.business_purpose

### Validation Checks

| Check | Status | Details |
|-------|--------|---------|
| Receipt Present | {% if receipt_check.has_receipt %}✅ Yes{% else %}❌ Missing{% endif %} | {{ receipt_check.message }} |
| Receipt Matches | {% if match_check.is_matching %}✅ Match{% else %}❌ Mismatch{% endif %} | Merchant: {% if match_check.merchant_matches %}✓{% else %}✗{% endif %}, Amount: {% if match_check.amount_matches %}✓{% else %}✗{% endif %}, Date: {% if match_check.date_matches %}✓{% else %}✗{% endif %} ({{ match_check.confidence }} confidence) |
| Spending Limit | {% if limit_check.within_limit %}✅ Within{% else %}❌ Exceeded{% endif %} | Limit: ${{ limit_check.limit_amount }} for {{ limit_check.seniority }} ({{ limit_check.category }}){% if not limit_check.within_limit %} - Exceeded by ${{ limit_check.exceeded_by }}{% endif %} |
| Weekday Expense | {% if weekend_check.is_weekday %}✅ Weekday{% else %}❌ Weekend{% endif %} | {{ weekend_check.day_of_week }} - {{ weekend_check.message }} |
| Reasonable Amount | {% if reasonable_check.is_reasonable %}✅ Reasonable{% else %}⚠️ Review{% endif %} | Expected: {{ reasonable_check.expected_range }} - {{ reasonable_check.assessment }} |

### Result

{% set has_critical_issue = not receipt_check.has_receipt or not match_check.is_matching or not limit_check.within_limit or not weekend_check.is_weekday %}
{% if has_critical_issue %}
**Status:** ❌ REJECTED
**Approved Amount:** $0.00

**Issues:**
{% if not receipt_check.has_receipt %}- Missing receipt - all expenses require receipt documentation
{% endif %}{% if not match_check.is_matching %}- Receipt does not match expense: {{ match_check.discrepancies }}
{% endif %}{% if not limit_check.within_limit %}- Exceeds spending limit for {{ limit_check.seniority }} level by ${{ limit_check.exceeded_by }}
{% endif %}{% if not weekend_check.is_weekday %}- Weekend expenses not permitted without prior approval
{% endif %}{% if not reasonable_check.is_reasonable %}- Amount flagged for review: {{ reasonable_check.assessment }}
{% endif %}
{% else %}
**Status:** ✅ APPROVED
**Approved Amount:** ${{ expense_with_receipt.expense.total_amount }}
{% if not reasonable_check.is_reasonable %}
**Note:** Amount flagged for review but approved: {{ reasonable_check.assessment }}
{% endif %}
{% endif %}
"""

[pipe.compose_final_report]
type = "PipeCompose"
description = "Composes the final validation report"
inputs = { report = "ExpenseReport", expense_validations = "Text[]" }
output = "Text"

[pipe.compose_final_report.template]
category = "markdown"
template = """
# Expense Report Validation

**Employee:** {{ report.employee.full_name }} (ID: {{ report.employee.employee_id }})
**Email:** {{ report.employee.email }}
**Department:** {{ report.employee.department }}
**Title:** {{ report.employee.job_title }}
**Seniority:** {{ report.employee.seniority }}

---

@expense_validations

---

## Summary

Total expenses submitted: {{ report.expenses_with_receipts | length }}

Review the individual expense validations above for detailed results.

---
*Validated by Expense Validator System*
"""
