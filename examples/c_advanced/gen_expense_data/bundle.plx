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

[concept.CompanyCategory]
description = "A type of company for expense generation with typical expense range"

[concept.CompanyCategory.structure]
category = { type = "text", description = "Company category type", choices = ["supermarket", "restaurant", "cafe", "hotel", "airline", "office_supplies", "pharmacy", "electronics", "gas_station", "delivery"], required = true }
typical_expense_range = { type = "text", description = "Typical expense range e.g. '20-80 USD'", required = true }

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
expense_category = { type = "text", description = "Expense category for this receipt", choices = ["Meals", "Travel", "Accommodation", "Equipment", "Supplies", "Transportation"], required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.Expense]
description = "An expense submitted for reimbursement"

[concept.Expense.structure]
expense_id = { type = "text", description = "Unique expense identifier", required = true }
category = { type = "text", description = "Expense category", choices = ["Meals", "Travel", "Accommodation", "Equipment", "Supplies", "Transportation"], required = true }
merchant_name = { type = "text", description = "Name of the merchant", required = true }
expense_date = { type = "date", description = "Date of the expense", required = true }
total_amount = { type = "number", description = "Total expense amount", required = true }
currency = { type = "text", description = "Currency code", required = true }
business_purpose = { type = "text", description = "Business justification for the expense", required = true }

[concept.ReceiptPrompt]
description = "A prompt optimized for generating a receipt image"
refines = "Text"

[concept.ExpenseWithReceipt]
description = "An expense paired with its receipt image URL"

[concept.ExpenseWithReceipt.structure]
expense = { type = "concept", concept_ref = "expense_data_generation.Expense", description = "The expense details", required = true }
receipt_url = { type = "text", description = "URL of the receipt image", required = true }

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
description = "Assigns 3 company categories appropriate for the employee's role and department"
inputs = { employee = "Employee" }
output = "CompanyCategory[3]"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator that assigns realistic expense categories based on employee roles.
"""
prompt = """
Based on this employee's role and department, select 3 different company categories where they would realistically have business expenses.

@employee

Guidelines:
- Choose categories that make sense for their job function
- Sales/Marketing: restaurants, hotels, airlines, cafes
- Engineering/Product: cafes, electronics, office_supplies
- Finance/Operations: office_supplies, delivery, supermarket
- Include variety - don't pick similar categories
- Set realistic expense ranges for each category
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
type = "PipeLLM"
description = "Generates the full text content of a receipt"
inputs = { employee = "Employee", company_profile = "CompanyProfile", company_category = "CompanyCategory" }
output = "ReceiptContent"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator creating realistic receipt content for expense reports.
"""
prompt = """
Generate a realistic receipt for this employee's expense at this company.

@employee

@company_profile

Expense range: $company_category.typical_expense_range

IMPORTANT FORMATTING RULES:
The receipt text must include ALL of these sections in order:

1. HEADER:
   - Company name (centered/prominent)
   - Full address
   - Phone number
   - Transaction/ticket number (format: TIC# XXXXX or #XXXXX)
   - Date and time (within last 30 days)

2. ITEMIZED LIST:
   - Select 2-6 realistic items from the product catalog
   - Format: QTY x ITEM NAME ... 12.99
   - For weighted items: 5.99/lb 0.5lb = 3.00

3. TOTALS SECTION:
   - Subtotal
   - Tax (calculate realistic tax ~8%)
   - TOTAL (must be within the expense range)

4. PAYMENT SECTION:
   - Payment method: "Card VISA ****1234" or similar
   - Status: APPROVED

Format the full_receipt_text as it would appear printed on thermal paper - use simple text formatting with spaces for alignment.

ALSO provide:
- The total_amount as a number
- Currency: "USD"
- The expense_date (within last 30 days)
- The expense_category: map to one of ["Meals", "Travel", "Accommodation", "Equipment", "Supplies", "Transportation"]
- A brief business_purpose based on the employee's role
"""

[pipe.generate_receipt_prompt]
type = "PipeLLM"
description = "Creates an image generation prompt for the receipt photo"
inputs = { receipt_content = "ReceiptContent", company_profile = "CompanyProfile" }
output = "ReceiptPrompt"
model = "@default-small"
system_prompt = """
You are an expert at creating image generation prompts for realistic receipt photos.
"""
prompt = """
Create an image generation prompt for a photo of this receipt:

Company: $company_profile.name
Category: $company_profile.category

Receipt content to show:

@receipt_content

CRITICAL REQUIREMENTS:
- The receipt MUST show the exact text content above - it must be READABLE
- Include a simple logo/brand mark at the top of the receipt appropriate for this type of business
- The receipt should be printed on white thermal paper
- This is a PHOTO of a receipt, not a scan

STYLE SELECTION (pick ONE randomly):

IMPERFECT STYLE (1/3 chance):
- Receipt slightly crumpled or with a small coffee stain in corner
- OR held by a hand / lying on a restaurant table
- Text must still be clearly readable

CLEAN STYLE (2/3 chance):
- Receipt flat on a plain surface (desk, table)
- Good lighting, slight angle
- Clean and crisp like a casual photo

Write 2-3 sentences describing the visual scene. Focus on the photo style, the receipt should display the exact content provided above.
"""

[pipe.render_receipt]
type = "PipeImgGen"
description = "Generates the final receipt image"
inputs = { receipt_prompt = "ReceiptPrompt" }
output = "Image"
model = "@best-gpt"
prompt = "$receipt_prompt"

[pipe.compose_expense_from_receipt]
type = "PipeCompose"
description = "Creates an Expense record from the receipt content"
inputs = { receipt_content = "ReceiptContent", company_profile = "CompanyProfile" }
output = "Expense"

[pipe.compose_expense_from_receipt.construct]
expense_id = { template = "EXP-{{ receipt_content.expense_date | replace('-', '') }}-0001" }
category = { from = "receipt_content.expense_category" }
merchant_name = { from = "company_profile.name" }
expense_date = { from = "receipt_content.expense_date" }
total_amount = { from = "receipt_content.total_amount" }
currency = { from = "receipt_content.currency" }
business_purpose = { from = "receipt_content.business_purpose" }

[pipe.compose_expense_with_receipt]
type = "PipeCompose"
description = "Pairs an expense with its generated receipt"
inputs = { expense = "Expense", receipt = "Image" }
output = "ExpenseWithReceipt"

[pipe.compose_expense_with_receipt.construct]
expense = { from = "expense" }
receipt_url = { from = "receipt.url" }

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
<p class="info"><strong>Department:</strong> {{ employee.department }} | <strong>Title:</strong> {{ employee.job_title }}</p>
<table>
<tr><th>Expense ID</th><th>Date</th><th>Category</th><th>Merchant</th><th>Purpose</th><th>Amount</th><th>Receipt</th></tr>
{% for item in expenses_with_receipts %}
<tr>
<td>{{ item.expense.expense_id }}</td>
<td>{{ item.expense.expense_date }}</td>
<td>{{ item.expense.category }}</td>
<td>{{ item.expense.merchant_name }}</td>
<td>{{ item.expense.business_purpose }}</td>
<td class="amount">{{ item.expense.currency }} {{ item.expense.total_amount }}</td>
<td><img src="{{ item.receipt_url }}"></td>
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
