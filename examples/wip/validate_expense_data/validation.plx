domain = "expense_validator"
description = "Validates expense reports against company policies and determines reimbursement eligibility"
main_pipe = "validate_expense_report"

# ============================================================================
# INPUT CONCEPTS
# ============================================================================

[concept.ExpenseReportPDF]
description = "A PDF document containing the expense report with employee info and expense line items"
refines = "Document"

[concept.ReceiptImage]
description = "A receipt image linked to an expense by expense_id in the filename"
refines = "Image"

# ============================================================================
# DATA CONCEPTS - EMPLOYEE
# ============================================================================

[concept.Employee]
description = "An employee who submitted the expense report"

[concept.Employee.structure]
employee_id = { type = "text", description = "Unique employee identifier (e.g., EMP-0001)", required = true }
full_name = { type = "text", description = "Employee full name", required = true }
email = { type = "text", description = "Employee email address", required = true }
department = { type = "text", description = "Department name", required = true }
job_title = { type = "text", description = "Job title", required = true }
seniority = { type = "text", description = "Employee seniority level", choices = ["Junior", "Senior", "Lead", "Manager", "Director", "VP", "Executive"], required = true }

# ============================================================================
# DATA CONCEPTS - EXPENSE
# ============================================================================

[concept.Expense]
description = "A single expense line item from the expense report"

[concept.Expense.structure]
expense_id = { type = "text", description = "Unique expense identifier (e.g., EXP-20260115-0001)", required = true }
expense_date = { type = "date", description = "Date of the expense", required = true }
category = { type = "text", description = "Expense category", choices = ["supermarket", "restaurant", "cafe", "hotel", "airline", "office_supplies", "pharmacy", "electronics", "gas_station", "delivery", "other"], required = true }
merchant = { type = "text", description = "Merchant or vendor name", required = true }
total_amount = { type = "number", description = "Total expense amount", required = true }
currency = { type = "text", description = "Currency code (e.g., USD)", required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.ExpenseReport]
description = "Complete parsed expense report with employee and all expenses"

[concept.ExpenseReport.structure]
employee = { type = "concept", concept_ref = "expense_validator.Employee", description = "The employee who submitted the report", required = true }
expenses = { type = "list", item_type = "concept", item_concept_ref = "expense_validator.Expense", description = "List of expenses from the report", required = true }

# ============================================================================
# VALIDATION RULE CONCEPTS
# ============================================================================

[concept.ReceiptMatchCheck]
description = "Vision LLM assessment of whether receipt matches the expense details"

[concept.ReceiptMatchCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
has_receipt = { type = "boolean", description = "Whether a receipt was provided for this expense", required = true }
is_matching = { type = "boolean", description = "Whether receipt matches expense (false if no receipt)", required = true }
extracted_merchant = { type = "text", description = "Merchant name extracted from the receipt image", required = true }
merchant_matches = { type = "boolean", description = "Merchant name on receipt matches claimed merchant", required = true }
amount_matches = { type = "boolean", description = "Amount on receipt matches claimed amount", required = true }
date_matches = { type = "boolean", description = "Date on receipt matches claimed date", required = true }
confidence = { type = "text", description = "Confidence level of the assessment", choices = ["high", "medium", "low"], required = true }
discrepancies = { type = "text", description = "Description of any discrepancies found" }

[concept.SpendingLimitCheck]
description = "Check if expense is within spending limits based on employee seniority and expense category"

[concept.SpendingLimitCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
within_limit = { type = "boolean", description = "Whether expense is within the allowed limit", required = true }
limit_amount = { type = "number", description = "The spending limit for this seniority/category", required = true }
claimed_amount = { type = "number", description = "The amount claimed", required = true }
exceeded_by = { type = "number", description = "Amount exceeded (0 if within limit)", required = true }
category = { type = "text", description = "The expense category checked", required = true }
seniority = { type = "text", description = "The employee seniority level", required = true }

[concept.WeekendCheck]
description = "Check if expense occurred on a weekend (company policy: no weekend expenses without prior approval)"

[concept.WeekendCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
is_weekday = { type = "boolean", description = "True if expense is on a weekday (Mon-Fri)", required = true }
day_of_week = { type = "text", description = "Day name (Monday, Tuesday, etc.)", required = true }
policy_status = { type = "text", description = "Policy compliance status", choices = ["compliant", "requires_approval", "violation"], required = true }
message = { type = "text", description = "Explanation of the check result", required = true }

[concept.PurposeQualityCheck]
description = "LLM assessment of whether the business purpose justification is adequate and professional"

[concept.PurposeQualityCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
is_adequate = { type = "boolean", description = "Whether the business purpose is adequately justified", required = true }
clarity_score = { type = "text", description = "Clarity of the justification", choices = ["excellent", "good", "acceptable", "insufficient", "missing"], required = true }
business_relevance = { type = "text", description = "How clearly the expense relates to business activities", choices = ["clearly_related", "possibly_related", "unclear", "unrelated"], required = true }
recommendation = { type = "text", description = "Recommendation for the expense", choices = ["approve", "approve_with_note", "request_clarification", "reject"], required = true }
assessment = { type = "text", description = "Detailed explanation of the assessment", required = true }

[concept.ReasonableAmountCheck]
description = "LLM assessment of whether expense amount is reasonable for the category and context"

[concept.ReasonableAmountCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
is_reasonable = { type = "boolean", description = "Whether the amount seems reasonable", required = true }
expected_range_min = { type = "number", description = "Lower bound of expected price range", required = true }
expected_range_max = { type = "number", description = "Upper bound of expected price range", required = true }
variance_category = { type = "text", description = "How the amount compares to expectations", choices = ["within_range", "slightly_high", "significantly_high", "slightly_low", "significantly_low"], required = true }
assessment = { type = "text", description = "Explanation of the assessment", required = true }

[concept.TimelinesCheck]
description = "Check if expense was submitted within the allowed timeframe (30 days from expense date)"

[concept.TimelinesCheck.structure]
expense_id = { type = "text", description = "The expense ID being checked", required = true }
is_timely = { type = "boolean", description = "Whether the expense was submitted within deadline", required = true }
days_since_expense = { type = "integer", description = "Number of days since the expense occurred", required = true }
submission_deadline = { type = "integer", description = "Maximum allowed days for submission", required = true }
policy_status = { type = "text", description = "Policy compliance status", choices = ["compliant", "late_but_acceptable", "too_late"], required = true }
message = { type = "text", description = "Explanation of the timeliness status", required = true }

# ============================================================================
# VALIDATION RESULT CONCEPTS
# ============================================================================

[concept.ExpenseValidationResult]
description = "Complete validation result for a single expense with detailed findings"

[concept.ExpenseValidationResult.structure]
expense_id = { type = "text", description = "The expense ID being validated", required = true }
expense_category = { type = "text", description = "The category of the expense", required = true }
expense_merchant = { type = "text", description = "The merchant name", required = true }
is_approved = { type = "boolean", description = "Whether the expense is approved for reimbursement", required = true }
approval_status = { type = "text", description = "Detailed approval status", choices = ["approved", "approved_with_warnings", "pending_clarification", "rejected"], required = true }
claimed_amount = { type = "number", description = "The amount claimed by the employee", required = true }
approved_amount = { type = "number", description = "The amount approved (0 if rejected, may be capped at limit)", required = true }
rejection_reasons = { type = "list", item_type = "text", description = "List of reasons for rejection (empty if approved)" }
warnings = { type = "list", item_type = "text", description = "List of warnings (expense approved but flagged)" }
action_required = { type = "text", description = "Any action required from employee or manager" }

[concept.ValidationReport]
description = "Final validation report with all expense results and executive summary"

[concept.ValidationReport.structure]
employee = { type = "concept", concept_ref = "expense_validator.Employee", description = "The employee who submitted the report", required = true }
expense_results = { type = "list", item_type = "concept", item_concept_ref = "expense_validator.ExpenseValidationResult", description = "Validation results for each expense", required = true }
total_claimed = { type = "number", description = "Total amount claimed", required = true }
total_approved = { type = "number", description = "Total amount approved for reimbursement", required = true }
total_rejected = { type = "number", description = "Total amount rejected", required = true }
total_pending = { type = "number", description = "Total amount pending clarification", required = true }
approval_rate = { type = "number", description = "Percentage of expenses fully approved", required = true }
expenses_approved = { type = "integer", description = "Number of expenses approved", required = true }
expenses_rejected = { type = "integer", description = "Number of expenses rejected", required = true }
expenses_pending = { type = "integer", description = "Number of expenses pending clarification", required = true }
summary_notes = { type = "text", description = "Executive summary notes for the finance team", required = true }

# ============================================================================
# MAIN VALIDATION PIPELINE
# ============================================================================

[pipe.validate_expense_report]
type = "PipeSequence"
description = "Main pipeline that validates an expense report from PDF and receipt images"
inputs = { expense_pdf = "ExpenseReportPDF", receipts = "ReceiptImage[]" }
output = "ValidationReport"
steps = [
    { pipe = "extract_pdf_content", result = "pages" },
    { pipe = "parse_expense_report", result = "report" },
    { pipe = "extract_expenses_list", result = "expenses" },
    { pipe = "validate_single_expense", batch_over = "expenses", batch_as = "expense", result = "expense_validations" },
    { pipe = "compose_validation_report", result = "validation_report" },
]

[pipe.extract_expenses_list]
type = "PipeFunc"
description = "Extracts the expenses list from the parsed expense report"
inputs = { report = "ExpenseReport", receipts = "ReceiptImage[]" }
output = "Expense[]"
function_name = "extract_expenses_list"

# ============================================================================
# EXTRACTION AND PARSING PIPES
# ============================================================================

[pipe.extract_pdf_content]
type = "PipeExtract"
description = "Extracts text and images from the expense report PDF"
inputs = { expense_pdf = "ExpenseReportPDF" }
output = "Page[]"

[pipe.parse_expense_report]
type = "PipeLLM"
description = "Parses the extracted PDF pages into structured expense report data"
inputs = { pages = "Page[]" }
output = "ExpenseReport"
model = { model = "best-claude", temperature = 0.1 }
prompt = """
Parse this expense report document into a structured ExpenseReport.

@pages

The document should contain:
1. Employee information: employee_id, full_name, email, department, job_title, seniority
2. A table of expense line items with: expense_id, expense_date, category, merchant, total_amount, currency, business_purpose

Extract all the data and return a complete ExpenseReport with:
- employee: The employee details
- expenses: List of all expense line items

IMPORTANT PARSING RULES:
- Parse dates in YYYY-MM-DD format
- Categories must be one of: meals, travel, accommodation, equipment, supplies, transportation, entertainment, other
- Seniority must be one of: Junior, Senior, Lead, Manager, Director, VP, Executive
- If a field is missing or unclear, make a reasonable inference based on context
- Ensure expense_id follows the format EXP-YYYYMMDD-NNNN if not explicitly provided
"""

# ============================================================================
# SINGLE EXPENSE VALIDATION
# ============================================================================

[pipe.validate_single_expense]
type = "PipeSequence"
description = "Validates a single expense against all company policies"
inputs = { report = "ExpenseReport", expense = "Expense", receipts = "ReceiptImage[]" }
output = "ExpenseValidationResult"
steps = [
    { pipe = "check_receipt_match", result = "receipt_check" },
    { pipe = "check_spending_limit", result = "limit_check" },
    { pipe = "check_weekend", result = "weekend_check" },
    { pipe = "check_timeliness", result = "timeliness_check" },
    { pipe = "check_purpose_quality", result = "purpose_check" },
    { pipe = "check_reasonable_amount", result = "reasonable_check" },
    { pipe = "compose_expense_result", result = "validation_result" },
]

# ============================================================================
# VALIDATION CHECK PIPES
# ============================================================================

[pipe.check_receipt_match]
type = "PipeLLM"
description = "Uses vision LLM to verify receipt matches expense details"
inputs = { expense = "Expense", receipts = "ReceiptImage[]" }
output = "ReceiptMatchCheck"
model = { model = "best-claude", temperature = 0.1 }
prompt = """
Verify if there is a receipt that matches this expense claim.

EXPENSE DETAILS:
- Expense ID: $expense.expense_id
- Merchant: $expense.merchant
- Amount: $expense.total_amount $expense.currency
- Date: $expense.expense_date
- Category: $expense.category

AVAILABLE RECEIPT IMAGES:

@receipts

VALIDATION INSTRUCTIONS:
1. First, check if any receipt image corresponds to this expense (look for expense_id in filename or matching details)
2. Set has_receipt=true only if you find a relevant receipt for this expense
3. If no receipt found: set is_matching=false, all matches=false, confidence="high", extracted_merchant="<UNKNOWN>", discrepancies="No receipt provided for expense $expense.expense_id"

4. If a receipt is found:
   - ALWAYS extract the merchant/store name from the receipt header and set extracted_merchant to that name
   - Verify if the merchant name on the receipt matches "$expense.merchant" (if expense merchant is "<UNKNOWN>", set merchant_matches=true)
   - Does the total amount match $expense.total_amount $expense.currency (allow for minor formatting differences)?
   - Does the date match or is within 1 day of $expense.expense_date?

5. Set confidence based on receipt quality:
   - "high": Clear, legible receipt with all details visible
   - "medium": Some details hard to read but main info visible
   - "low": Poor quality, hard to verify details

6. List any discrepancies found in detail.

IMPORTANT: Always extract and return the merchant name from the receipt in extracted_merchant field.

Return expense_id as "$expense.expense_id" in your response.
"""

[pipe.check_spending_limit]
type = "PipeFunc"
description = "Checks if expense is within spending limits based on seniority and category"
inputs = { report = "ExpenseReport", expense = "Expense" }
output = "SpendingLimitCheck"
function_name = "check_spending_limit"

[pipe.check_weekend]
type = "PipeFunc"
description = "Checks if expense occurred on a weekend (requires prior approval per company policy)"
inputs = { expense = "Expense" }
output = "WeekendCheck"
function_name = "check_weekend"

[pipe.check_timeliness]
type = "PipeFunc"
description = "Checks if expense was submitted within the allowed timeframe"
inputs = { expense = "Expense" }
output = "TimelinesCheck"
function_name = "check_timeliness"

[pipe.check_purpose_quality]
type = "PipeLLM"
description = "Assesses the quality and adequacy of the business purpose justification"
inputs = { expense = "Expense", report = "ExpenseReport" }
output = "PurposeQualityCheck"
model = { model = "best-claude", temperature = 0.2 }
system_prompt = """
You are a corporate expense auditor reviewing business purpose justifications. Your role is to ensure expenses have adequate documentation for compliance and audit purposes.

COMPANY POLICY ON BUSINESS PURPOSE:
- All expenses must have a clear business justification
- The purpose should explain HOW the expense relates to company business
- Generic statements like "business expense" or "work related" are insufficient
- Meals with clients/partners should mention who was present and the business topic
- Travel should specify the destination, purpose, and expected business outcome
- Equipment/supplies should explain the business need

CLARITY SCORING:
- excellent: Specific details, clear business connection, names/projects mentioned
- good: Clear purpose with reasonable detail
- acceptable: Basic justification provided, could use more detail
- insufficient: Vague or generic, does not explain business relevance
- missing: No purpose provided or completely uninformative

BUSINESS RELEVANCE:
- clearly_related: Obvious business connection (client meeting, project work, etc.)
- possibly_related: Could be business-related but unclear
- unclear: Cannot determine if business-related
- unrelated: Appears to be personal expense
"""
prompt = """
Assess the business purpose justification for this expense:

@expense

@report

Evaluate:
1. Is the business purpose clearly stated and specific?
2. Does it adequately explain the business need?
3. Is it appropriate for the employee's role and department?
4. Would this justification satisfy an external auditor?

Provide your recommendation:
- approve: Purpose is clear and business-relevant
- approve_with_note: Acceptable but could be improved for future submissions
- request_clarification: Need more details before approval
- reject: Purpose is inadequate or appears non-business related

Return expense_id as "$expense.expense_id" in your response.
"""

[pipe.check_reasonable_amount]
type = "PipeLLM"
description = "Assesses if expense amount is reasonable for the category and business context"
inputs = { expense = "Expense", report = "ExpenseReport" }
output = "ReasonableAmountCheck"
model = { model = "best-claude", temperature = 0.2 }
system_prompt = """
You are an expense auditor assessing whether expense amounts are reasonable based on typical business costs and context.

TYPICAL PRICE RANGES BY CATEGORY (USD):
- meals: $10-50 (solo), $30-100 (with colleagues), $75-300 (client entertainment)
- travel: $200-800 (domestic flights), $500-2500 (international flights)
- accommodation: $100-250 (standard), $200-450 (major cities), up to $600 (premium markets)
- equipment: $50-500 (accessories), $500-2000 (computers/devices)
- supplies: $10-100 (office supplies), $50-300 (specialized items)
- transportation: $15-75 (rideshare/taxi), $50-150 (car rental per day)
- entertainment: $50-200 (team events), $100-500 (client entertainment)
- other: varies widely, assess based on description

CONTEXT FACTORS TO CONSIDER:
- Employee seniority (executives may have higher-tier expenses)
- Location (major cities cost more)
- Business purpose (client-facing may justify premium services)
- Department (sales/BD may have higher entertainment budgets)

Flag as unreasonable ONLY if the amount is significantly outside normal ranges without apparent justification.
"""
prompt = """
Assess if this expense amount is reasonable:

@expense

@report

Determine:
1. What is the expected price range for this type of expense?
2. Is the amount within, slightly above, or significantly above that range?
3. Does the context (seniority, purpose, location if mentioned) justify any premium?

Provide expected_range_min and expected_range_max as numbers.

Classify variance_category:
- within_range: Amount is within expected range
- slightly_high: 10-30% above expected range
- significantly_high: More than 30% above expected range
- slightly_low: Unusually low (may indicate missing items)
- significantly_low: Very low (verify receipt completeness)

Return expense_id as "$expense.expense_id" in your response.
"""

# ============================================================================
# RESULT COMPOSITION PIPES
# ============================================================================

[pipe.compose_expense_result]
type = "PipeFunc"
description = "Composes the final validation result for a single expense based on all checks"
inputs = { expense = "Expense", receipt_check = "ReceiptMatchCheck", limit_check = "SpendingLimitCheck", weekend_check = "WeekendCheck", timeliness_check = "TimelinesCheck", purpose_check = "PurposeQualityCheck", reasonable_check = "ReasonableAmountCheck" }
output = "ExpenseValidationResult"
function_name = "compose_expense_result"

[pipe.compose_validation_report]
type = "PipeFunc"
description = "Composes the final validation report with summary statistics and executive notes"
inputs = { report = "ExpenseReport", expense_validations = "ExpenseValidationResult[]" }
output = "ValidationReport"
function_name = "compose_validation_report"
