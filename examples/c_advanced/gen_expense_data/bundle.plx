domain = "expense_data_generation"
description = "Generating synthetic expense data with realistic receipts"
main_pipe = "generate_expense_dataset"

# ============================================================================
# INPUT CONCEPTS
# ============================================================================

[concept.NbOfEmployees]
description = "How many employees to generate"
refines = "Number"

# ============================================================================
# DATA CONCEPTS
# ============================================================================

[concept.Employee]
description = "An employee who can submit expense reports"

[concept.Employee.structure]
employee_id = { type = "text", description = "Unique employee identifier", required = true }
full_name = { type = "text", description = "Employee full name", required = true }
email = { type = "text", description = "Employee email address", required = true }
department = { type = "text", description = "Department name", required = true }
job_title = { type = "text", description = "Job title", required = true }
seniority = { type = "text", description = "Employee seniority level", choices = ["Junior", "Senior", "Lead", "Manager", "Director", "VP", "Executive"], required = true }

[concept.ExpenseScenario]
description = "Defines whether an expense is legitimate or contains fraud indicators"

[concept.ExpenseScenario.structure]
scenario_type = { type = "text", description = "Type of expense scenario", choices = ["legitimate", "weekend_expense", "inflated_amount", "personal_expense", "vague_purpose"], required = true }
fraud_description = { type = "text", description = "Description of the fraud indicator if not legitimate" }
target_date = { type = "text", description = "Specific date to use for the expense (YYYY-MM-DD format), especially for weekend scenarios" }
amount_multiplier = { type = "number", description = "Multiplier for inflated amounts (1.0 for normal, 2.0+ for inflated)", default_value = 1.0 }

[concept.CompanyCategory]
description = "A type of company for expense generation with typical expense range"

[concept.CompanyCategory.structure]
category = { type = "text", description = "Company category type", choices = ["supermarket", "restaurant", "cafe", "hotel", "airline", "office_supplies", "pharmacy", "electronics", "gas_station", "delivery"], required = true }
typical_expense_range = { type = "text", description = "Typical expense range e.g. '20-80 USD'", required = true }
expense_scenario = { type = "concept", concept_ref = "expense_data_generation.ExpenseScenario", description = "The fraud scenario for this expense", required = true }

[concept.CompanyProfile]
description = "A company with its details and product catalog"

[concept.CompanyProfile.structure]
name = { type = "text", description = "Company name", required = true }
category = { type = "text", description = "Company category type", required = true }
address = { type = "text", description = "Street address", required = true }
city = { type = "text", description = "City name", required = true }
postal_code = { type = "text", description = "Postal/ZIP code", required = true }
country = { type = "text", description = "Country name", required = true }
phone = { type = "text", description = "Phone number", required = true }
website = { type = "text", description = "Website URL" }
tax_id = { type = "text", description = "Tax identification number" }
product_catalog = { type = "text", description = "List of products/services with typical prices", required = true }

[concept.ReceiptContent]
description = "The full text content of a receipt with metadata"

[concept.ReceiptContent.structure]
full_receipt_text = { type = "text", description = "Complete formatted receipt text including header, items, totals", required = true }
total_amount = { type = "number", description = "Total amount on the receipt", required = true }
currency = { type = "text", description = "Currency code", required = true }
expense_date = { type = "date", description = "Date of the transaction", required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.PurchasedItem]
description = "An item purchased on a receipt"

[concept.PurchasedItem.structure]
name = { type = "text", description = "Item name from catalog", required = true }
quantity = { type = "integer", description = "Quantity purchased", required = true }
unit_price = { type = "number", description = "Price per unit", required = true }
line_total = { type = "number", description = "Total for this line (quantity * unit_price)", required = true }
currency = { type = "text", description = "Currency code (always USD)", required = true }

[concept.ReceiptItemsAndTotals]
description = "Items purchased and calculated totals for a receipt"

[concept.ReceiptItemsAndTotals.structure]
items = { type = "list", item_type = "concept", item_concept_ref = "expense_data_generation.PurchasedItem", description = "List of purchased items" }
subtotal = { type = "number", description = "Sum of all line totals", required = true }
tax_rate = { type = "number", description = "Tax rate as decimal (e.g., 0.08 for 8%)", required = true }
tax_amount = { type = "number", description = "Calculated tax amount", required = true }
total_amount = { type = "number", description = "Final total (subtotal + tax)", required = true }
currency = { type = "text", description = "Currency code (always USD)", required = true }

[concept.ReceiptHeader]
description = "Header information for a receipt"

[concept.ReceiptHeader.structure]
transaction_number = { type = "text", description = "Transaction/ticket number (format: TIC# XXXXX)", required = true }
transaction_date = { type = "date", description = "Date of transaction (must be in January 2026)", required = true }
transaction_time = { type = "text", description = "Time of transaction (format: HH:MM AM/PM)", required = true }

[concept.ExpenseMetadata]
description = "Business metadata for an expense"

[concept.ExpenseMetadata.structure]
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.Expense]
description = "An expense submitted for reimbursement"

[concept.Expense.structure]
expense_id = { type = "text", description = "Unique expense identifier", required = true }
expense_date = { type = "date", description = "Date of the expense", required = true }
category = { type = "text", description = "Expense category", choices = ["supermarket", "restaurant", "cafe", "hotel", "airline", "office_supplies", "pharmacy", "electronics", "gas_station", "delivery"], required = true }
merchant = { type = "text", description = "Merchant or vendor name", required = true }
total_amount = { type = "number", description = "Total expense amount", required = true }
currency = { type = "text", description = "Currency code", required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.ReceiptPrompt]
description = "A prompt optimized for generating a receipt image"
refines = "Text"

[concept.Receipt]
description = "A receipt image for an expense"
refines = "Image"

[concept.ExpenseWithReceipt]
description = "An expense paired with its receipt image"

[concept.ExpenseWithReceipt.structure]
expense = { type = "concept", concept_ref = "expense_data_generation.Expense", description = "The expense details", required = true }
receipt = { type = "concept", concept_ref = "expense_data_generation.Receipt", description = "The receipt image", required = true }

[concept.EmployeeExpenseReport]
description = "An employee with their list of expenses, receipts, and HTML report"

[concept.EmployeeExpenseReport.structure]
employee = { type = "concept", concept_ref = "expense_data_generation.Employee", description = "The employee", required = true }
expenses_with_receipts = { type = "list", item_type = "concept", item_concept_ref = "expense_data_generation.ExpenseWithReceipt", description = "List of expenses with receipts", required = true }
html_report = { type = "concept", concept_ref = "Html", description = "HTML formatted expense report", required = true }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

[pipe.generate_expense_dataset]
type = "PipeSequence"
description = "Main pipeline that generates synthetic expense data for multiple employees."
inputs = { nb_employees = "NbOfEmployees" }
output = "EmployeeExpenseReport[]"
steps = [
    { pipe = "generate_employees", result = "employees" },
    { pipe = "generate_employee_report", batch_over = "employees", batch_as = "employee", result = "reports" },
]

[pipe.generate_employees]
type = "PipeLLM"
description = "Generates diverse employee profiles"
inputs = { nb_employees = "NbOfEmployees" }
output = "Employee[]"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator creating realistic employee profiles.
"""
prompt = """
Generate $nb_employees diverse employee profiles for a tech company.

Guidelines:
- Generate realistic names with diverse ethnicities and genders
- Email format: firstname.lastname at acmecorp.com
- Departments: Engineering, Marketing, Sales, Finance, Product
- Job titles should vary (Manager, Senior, Lead, Director, etc.)
- Each employee should have a unique employee_id (format: EMP-XXXX)
- Assign appropriate seniority levels: Junior, Senior, Lead, Manager, Director, VP, Executive
- Seniority should align with job title (e.g., "Senior Engineer" = Senior, "VP of Sales" = VP)
"""

[pipe.generate_employee_report]
type = "PipeSequence"
description = "Generates expenses with realistic receipts and HTML report for a single employee"
inputs = { employee = "Employee" }
output = "EmployeeExpenseReport"
steps = [
    { pipe = "generate_company_assignments", result = "company_categories" },
    { pipe = "generate_receipt_for_category", batch_over = "company_categories", batch_as = "company_category", result = "expenses_with_receipts" },
    { pipe = "render_expense_report_html", result = "html_report" },
    { pipe = "compose_employee_report", result = "report" },
]

# ============================================================================
# COMPANY ASSIGNMENT
# ============================================================================

[pipe.generate_company_assignments]
type = "PipeLLM"
description = "Assigns 3-4 company categories with a mix of legitimate and fraudulent expense scenarios"
inputs = { employee = "Employee" }
output = "CompanyCategory[]"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator creating expense scenarios for testing expense validation systems.
You must create a mix of legitimate expenses AND fraudulent/problematic expenses that should be flagged or rejected.
"""
prompt = """
Based on this employee's role and department, generate 3 OR 4 expense scenarios - some legitimate and some with fraud indicators.

@employee

JANUARY 2026 WEEKEND DATES (Saturday/Sunday):
- January 3-4 (Sat-Sun)
- January 10-11 (Sat-Sun)
- January 17-18 (Sat-Sun)
- January 24-25 (Sat-Sun)
- January 31 (Sat) - February 1 (Sun)

GENERATE EITHER 3 OR 4 EXPENSES (randomly choose):

If generating 3 expenses, include:
1. ONE legitimate expense (scenario_type = "legitimate")
2. ONE weekend expense (scenario_type = "weekend_expense") - use a weekend date from above
3. ONE of: inflated_amount, personal_expense, OR vague_purpose

If generating 4 expenses, include:
1. ONE legitimate expense (scenario_type = "legitimate")
2. ONE weekend expense (scenario_type = "weekend_expense") - use a weekend date from above
3. ONE inflated amount OR personal expense (scenario_type = "inflated_amount" or "personal_expense")
4. ONE with vague purpose (scenario_type = "vague_purpose")

FOR EACH CompanyCategory, provide:
- category: appropriate business category
- typical_expense_range: normal range for this category
- expense_scenario with:
  - scenario_type: one of the types above
  - fraud_description: explain the issue (empty for legitimate)
  - target_date: REQUIRED for weekend_expense (use format "2026-01-11" for a Saturday), optional otherwise
  - amount_multiplier: 1.0 for normal, 2.0-3.0 for inflated_amount scenarios

FRAUD SCENARIO DETAILS:

1. weekend_expense: Expense on Saturday or Sunday without prior approval
   - target_date MUST be a weekend date like "2026-01-04", "2026-01-11", "2026-01-18", or "2026-01-25"
   - fraud_description: "Weekend expense without prior manager approval"

2. inflated_amount: Amount significantly exceeds reasonable limits
   - amount_multiplier: 2.0 to 3.0
   - fraud_description: "Amount exceeds spending limit for employee seniority"

3. personal_expense: Personal purchase disguised as business
   - Use categories like electronics, pharmacy, supermarket
   - fraud_description: "Personal items claimed as business expense"

4. vague_purpose: Missing or inadequate business justification
   - fraud_description: "Vague or missing business purpose"

CATEGORY GUIDELINES:
- Sales/Marketing: restaurants, hotels, airlines, cafes
- Engineering/Product: cafes, electronics, office_supplies
- Finance/Operations: office_supplies, delivery, supermarket
"""

# ============================================================================
# RECEIPT GENERATION FOR EACH CATEGORY
# ============================================================================

[pipe.generate_receipt_for_category]
type = "PipeSequence"
description = "Generates a company profile, logo, receipt content, and final receipt image for one category"
inputs = { employee = "Employee", company_category = "CompanyCategory" }
output = "ExpenseWithReceipt"
steps = [
    { pipe = "generate_company_profile", result = "company_profile" },
    { pipe = "generate_receipt_content", result = "receipt_content" },
    { pipe = "generate_receipt_prompt", result = "receipt_prompt" },
    { pipe = "render_receipt", result = "receipt" },
    { pipe = "compose_expense_from_receipt", result = "expense" },
    { pipe = "compose_expense_with_receipt", result = "expense_with_receipt" },
]

[pipe.generate_company_profile]
type = "PipeLLM"
description = "Generates a realistic company profile with product catalog"
inputs = { company_category = "CompanyCategory" }
output = "CompanyProfile"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator creating realistic company profiles for expense receipts.
"""
prompt = """
Generate a realistic company profile for this type of business:

@company_category

Guidelines:
- Create a believable company name (can be inspired by real chains but not exact copies)
- Use a realistic US address with proper formatting
- Include a valid-looking phone number (format: (XXX) XXX-XXXX)
- Generate a realistic tax ID (format: XX-XXXXXXX)
- Create a product catalog with 8-15 items typical for this business type
- Each product should have a name and realistic price
- Format the product catalog as a simple list, one item per line: "Product Name - 12.99"

Examples of product catalogs by category:
- Restaurant: "Cheeseburger - 12.50", "Caesar Salad - 9.00", "Craft Beer - 7.00"
- Supermarket: "Organic Milk 1gal - 5.99", "Sourdough Bread - 4.50", "Free Range Eggs - 6.99"
- Cafe: "Espresso - 3.50", "Cappuccino - 4.75", "Avocado Toast - 11.00"
"""

[pipe.generate_receipt_content]
type = "PipeSequence"
description = "Generates the full text content of a receipt in multiple steps, respecting fraud scenarios"
inputs = { employee = "Employee", company_profile = "CompanyProfile", company_category = "CompanyCategory" }
output = "ReceiptContent"
steps = [
    { pipe = "generate_receipt_header", result = "receipt_header" },
    { pipe = "generate_receipt_items_and_totals", result = "items_and_totals" },
    { pipe = "generate_expense_metadata", result = "expense_metadata" },
    { pipe = "format_receipt_text", result = "formatted_receipt" },
    { pipe = "compose_receipt_content", result = "receipt_content" },
]

[pipe.generate_receipt_header]
type = "PipeLLM"
description = "Generates receipt header with transaction details, respecting scenario target dates"
inputs = { company_profile = "CompanyProfile", company_category = "CompanyCategory" }
output = "ReceiptHeader"
model = "$synthesizing-data"
prompt = """
Generate receipt header information for a transaction at this company:

Company: $company_profile.name

Expense Scenario: $company_category.expense_scenario.scenario_type
Target Date: $company_category.expense_scenario.target_date

Generate:
- A transaction number (format: TIC# followed by 5 digits, e.g., TIC# 48291)
- A transaction date:
  * If Target Date is provided and not empty, you MUST use exactly that date
  * If Target Date is empty/null, use a random WEEKDAY in January 2026 (avoid weekends: 3-4, 10-11, 17-18, 24-25, 31)
- A transaction time (format: HH:MM AM/PM, e.g., 2:34 PM)

CRITICAL: For weekend_expense scenarios, the target_date will be a weekend date like 2026-01-04 or 2026-01-11. You MUST use this exact date.
"""

[pipe.generate_receipt_items_and_totals]
type = "PipeLLM"
description = "Selects items from catalog and calculates totals, applying amount multiplier for fraud scenarios"
inputs = { company_profile = "CompanyProfile", company_category = "CompanyCategory" }
output = "ReceiptItemsAndTotals"
model = "$synthesizing-data"
prompt = """
Select items from this company's catalog and calculate the receipt totals.

@company_profile

Target expense range: $company_category.typical_expense_range
Expense Scenario Type: $company_category.expense_scenario.scenario_type
Amount Multiplier: $company_category.expense_scenario.amount_multiplier

Instructions:
1. Select 2-6 items from the product_catalog above
2. For EACH item, you MUST specify:
   - name: item name from catalog
   - quantity: usually 1-3
   - unit_price: price from catalog
   - line_total: quantity * unit_price
   - currency: MUST be "USD" for EVERY item
3. Calculate subtotal = sum of all line_totals
4. Apply tax_rate of 0.08 (8%)
5. Calculate tax_amount = subtotal * tax_rate (round to 2 decimals)
6. Calculate total_amount = subtotal + tax_amount

AMOUNT ADJUSTMENT FOR FRAUD SCENARIOS:
- If Amount Multiplier > 1.0, multiply ALL prices by this multiplier to inflate the receipt
- For "inflated_amount" scenarios, the final total should be 2-3x the normal range
- For "personal_expense" scenarios, include items that look personal (snacks, personal care, etc.)

CRITICAL REQUIREMENTS:
- EVERY item MUST have currency = "USD"
- The totals section MUST have currency = "USD"
- For legitimate scenarios: total_amount should be within the target expense range
- For inflated_amount scenarios: total_amount should EXCEED typical limits (use the multiplier)
- All amounts must be positive numbers with max 2 decimal places
"""

[pipe.generate_expense_metadata]
type = "PipeLLM"
description = "Determines business purpose based on expense scenario (legitimate or fraudulent)"
inputs = { employee = "Employee", company_profile = "CompanyProfile", company_category = "CompanyCategory" }
output = "ExpenseMetadata"
model = "$synthesizing-data"
prompt = """
Determine the business purpose for this transaction based on the expense scenario.

@employee

Company: $company_profile.name
Category: $company_profile.category

Expense Scenario Type: $company_category.expense_scenario.scenario_type
Fraud Description: $company_category.expense_scenario.fraud_description

WRITE THE BUSINESS PURPOSE BASED ON THE SCENARIO TYPE:

1. If scenario_type = "legitimate":
   Write a clear, specific business purpose that makes sense for this employee's job function.
   Examples:
   - "Team lunch meeting to discuss Q4 roadmap with 5 engineers"
   - "Client dinner with Acme Corp representatives to finalize contract"
   - "Office supplies for project documentation and quarterly reports"

2. If scenario_type = "weekend_expense":
   Write a business purpose that tries to justify a weekend expense but lacks prior approval mention.
   Examples:
   - "Urgent client meeting on Saturday"
   - "Weekend work session with team"

3. If scenario_type = "personal_expense":
   Write a vague business purpose that poorly disguises a personal purchase.
   Examples:
   - "Supplies for home office setup"
   - "Wellness items for productivity"
   - "Personal development materials"
   - "Snacks for the team" (but actually personal groceries)

4. If scenario_type = "vague_purpose":
   Write a very vague, non-specific purpose that doesn't explain the business need.
   Examples:
   - "Business expense"
   - "Work related"
   - "Misc"
   - "Various items"
   - "General supplies"

5. If scenario_type = "inflated_amount":
   Write a legitimate-sounding purpose (the fraud is in the amount, not the purpose).
   Examples: Same as legitimate
"""

[pipe.format_receipt_text]
type = "PipeCompose"
description = "Formats the receipt as thermal paper text"
inputs = { company_profile = "CompanyProfile", receipt_header = "ReceiptHeader", items_and_totals = "ReceiptItemsAndTotals" }
output = "Text"

[pipe.format_receipt_text.template]
category = "basic"
template = """
================================
      $company_profile.name
================================
$company_profile.address
$company_profile.city, $company_profile.postal_code
Tel: $company_profile.phone
--------------------------------
$receipt_header.transaction_number
$receipt_header.transaction_date $receipt_header.transaction_time
--------------------------------
{% for item in items_and_totals.items %}
{{ item.name }}              ${{ item.line_total | round(2) }}
{% endfor %}
--------------------------------
SUBTOTAL             ${{ items_and_totals.subtotal | round(2) }}
TAX {{ (items_and_totals.tax_rate * 100) | round(0) | int }}%                ${{ items_and_totals.tax_amount | round(2) }}
TOTAL                ${{ items_and_totals.total_amount | round(2) }}
================================
VISA ****1234
APPROVED
================================
     Thank you for your visit!
================================
"""

[pipe.compose_receipt_content]
type = "PipeCompose"
description = "Assembles the final ReceiptContent from all parts"
inputs = { formatted_receipt = "Text", items_and_totals = "ReceiptItemsAndTotals", receipt_header = "ReceiptHeader", expense_metadata = "ExpenseMetadata" }
output = "ReceiptContent"

[pipe.compose_receipt_content.construct]
full_receipt_text = { from = "formatted_receipt" }
total_amount = { from = "items_and_totals.total_amount" }
currency = { from = "items_and_totals.currency" }
expense_date = { from = "receipt_header.transaction_date" }
business_purpose = { from = "expense_metadata.business_purpose" }

[pipe.generate_receipt_prompt]
type = "PipeLLM"
description = "Creates an image generation prompt for the receipt photo"
inputs = { receipt_content = "ReceiptContent", company_profile = "CompanyProfile" }
output = "ReceiptPrompt"
model = "@default-small"
system_prompt = """
You are an expert at creating image generation prompts for realistic receipt photos.
Your prompts MUST include the COMPLETE receipt text that should appear on the receipt.
"""
prompt = """
Create an image generation prompt for a photo of a thermal paper receipt.

Company: $company_profile.name ($company_profile.category)
Location: $company_profile.address, $company_profile.city

=== EXACT RECEIPT TEXT TO DISPLAY (COPY THIS VERBATIM) ===

$receipt_content.full_receipt_text

=== END OF RECEIPT TEXT ===

CRITICAL REQUIREMENTS FOR YOUR PROMPT:
1. Your prompt MUST include ALL the text above EXACTLY as written - every line, every number, every detail
2. The receipt text must be READABLE and LEGIBLE in the generated image
3. Include a simple logo/brand mark at the top appropriate for a $company_profile.category business
4. The receipt is printed on white thermal paper (the typical thin paper from cash registers)
5. This is a PHOTO of a receipt, not a digital scan

PHOTO STYLE (pick ONE):

STYLE A - IMPERFECT (use this 80% of the time):
- Receipt slightly crumpled or with a small fold
- Maybe a tiny coffee stain in one corner
- Held by a hand, or on a slightly messy surface
- Natural lighting, slight shadows
- Text must still be clearly readable despite imperfections

STYLE B - CLEAN (use this 20% of the time):
- Receipt flat on a plain surface (wooden desk, clean table)
- Good even lighting with soft shadows
- Slight angle (not perfectly top-down)
- Fresh and crisp like just printed

Your prompt must be 3-5 sentences that:
1. Describe the photo scene and style
2. INCLUDE THE COMPLETE RECEIPT TEXT from above
3. Specify that text must be sharp and readable
"""

[pipe.render_receipt]
type = "PipeImgGen"
description = "Generates the final receipt image"
inputs = { receipt_prompt = "ReceiptPrompt" }
output = "Receipt"
model = "@best-gpt"
prompt = "$receipt_prompt"

[pipe.compose_expense_from_receipt]
type = "PipeCompose"
description = "Creates an Expense record from the receipt content and company profile"
inputs = { receipt_content = "ReceiptContent", company_profile = "CompanyProfile" }
output = "Expense"

[pipe.compose_expense_from_receipt.construct]
expense_id = { template = "EXP-{{ receipt_content.expense_date.strftime('%Y%m%d') }}-0001" }
expense_date = { from = "receipt_content.expense_date" }
category = { from = "company_profile.category" }
merchant = { from = "company_profile.name" }
total_amount = { from = "receipt_content.total_amount" }
currency = { from = "receipt_content.currency" }
business_purpose = { from = "receipt_content.business_purpose" }

[pipe.compose_expense_with_receipt]
type = "PipeCompose"
description = "Pairs an expense with its generated receipt"
inputs = { expense = "Expense", receipt = "Receipt" }
output = "ExpenseWithReceipt"

[pipe.compose_expense_with_receipt.construct]
expense = { from = "expense" }
receipt = { from = "receipt" }

[pipe.render_expense_report_html]
type = "PipeCompose"
description = "Renders an HTML expense report for an employee"
inputs = { employee = "Employee", expenses_with_receipts = "ExpenseWithReceipt[]" }
output = "Html"

[pipe.render_expense_report_html.template]
category = "html"
template = """
<html lang="en">
<head>
<title>Expense Report - {{ employee.full_name }}</title>
<style>
body { font-family: Arial, sans-serif; font-size: 10pt; margin: 0; }
h1 { color: #2c3e50; font-size: 18pt; border-bottom: 2px solid #4472C4; padding-bottom: 8px; margin-bottom: 5px; }
h2 { color: #34495e; font-size: 14pt; margin: 0 0 10px 0; }
.info { color: #555; margin: 2px 0; font-size: 9pt; }
table { width: 100%; border-collapse: collapse; margin-top: 15px; }
th, td { border: 1px solid #ccc; padding: 6px; text-align: left; vertical-align: middle; font-size: 9pt; }
th { background-color: #4472C4; color: white; }
tr:nth-child(even) { background-color: #f5f5f5; }
img { width: 50px; height: 50px; object-fit: cover; display: block; }
.amount { text-align: right; white-space: nowrap; }
</style>
</head>
<body>
<h1>Expense Report</h1>
<h2>{{ employee.full_name }}</h2>
<p class="info"><strong>ID:</strong> {{ employee.employee_id }} | <strong>Email:</strong> {{ employee.email }}</p>
<p class="info"><strong>Department:</strong> {{ employee.department }} | <strong>Title:</strong> {{ employee.job_title }} | <strong>Seniority:</strong> {{ employee.seniority }}</p>
<table>
<tr><th>Expense ID</th><th>Date</th><th>Category</th><th>Merchant</th><th>Purpose</th><th>Amount</th><th>Receipt</th></tr>
{% for item in expenses_with_receipts %}
<tr>
<td>{{ item.expense.expense_id }}</td>
<td>{{ item.expense.expense_date.strftime('%Y-%m-%d') }}</td>
<td>{{ item.expense.category }}</td>
<td>{{ item.expense.merchant }}</td>
<td>{{ item.expense.business_purpose }}</td>
<td class="amount">{{ item.expense.currency }} {{ item.expense.total_amount }}</td>
<td><img src="{{ item.receipt.public_url }}"></td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

[pipe.compose_employee_report]
type = "PipeCompose"
description = "Assembles the final employee expense report with HTML"
inputs = { employee = "Employee", expenses_with_receipts = "ExpenseWithReceipt[]", html_report = "Html" }
output = "EmployeeExpenseReport"

[pipe.compose_employee_report.construct]
employee = { from = "employee" }
expenses_with_receipts = { from = "expenses_with_receipts" }
html_report = { from = "html_report" }
