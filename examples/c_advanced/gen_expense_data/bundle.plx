domain = "expense_data_generation"
description = "Generating synthetic expense data"
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

[concept.Expense]
description = "An expense submitted for reimbursement"

[concept.Expense.structure]
expense_id = { type = "text", description = "Unique expense identifier", required = true }
category = { type = "text", description = "Expense category", choices = ["Meals", "Travel", "Accommodation", "Equipment"], required = true }
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
description = "Generates expenses with receipts and HTML report for a single employee"
inputs = { employee = "Employee" }
output = "EmployeeExpenseReport"
steps = [
    { pipe = "generate_expenses", result = "expenses" },
    { pipe = "generate_expense_with_receipt", batch_over = "expenses", batch_as = "expense", result = "expenses_with_receipts" },
    { pipe = "render_expense_report_html", result = "html_report" },
    { pipe = "compose_employee_report", result = "report" },
]

[pipe.generate_expenses]
type = "PipeLLM"
description = "Generates multiple expense records for an employee"
inputs = { employee = "Employee" }
output = "Expense[]"
model = "$synthesizing-data"
system_prompt = """
You are a synthetic data generator creating realistic expense records.
"""
prompt = """
Generate between 2 and 5 expenses appropriate for this employee's role and department.

@employee

Guidelines:
- Generate unique expense_id for each (format: EXP-YYYYMMDD-XXXX)
- Use varied categories appropriate for the employee's role
- Use realistic merchant names
- Expense dates should be within the last 30 days
- Amounts should be realistic (meals: $15-80, travel: $50-500)
- Use USD as currency
- Each expense needs a clear business purpose
"""

[pipe.generate_expense_with_receipt]
type = "PipeSequence"
description = "Generates a receipt image for an expense"
inputs = { expense = "Expense" }
output = "ExpenseWithReceipt"
steps = [
    { pipe = "generate_receipt_prompt", result = "receipt_prompt" },
    { pipe = "render_receipt", result = "receipt" },
    { pipe = "compose_expense_with_receipt", result = "expense_with_receipt" },
]

[pipe.generate_receipt_prompt]
type = "PipeLLM"
description = "Creates an image generation prompt for a receipt"
inputs = { expense = "Expense" }
output = "ReceiptPrompt"
model = "@default-small"
system_prompt = """
You are an expert at creating image generation prompts.
"""
prompt = """
Create an image generation prompt for a receipt based on this expense:

@expense

Describe a realistic receipt with the merchant name visible. Keep it concise.
"""

[pipe.render_receipt]
type = "PipeImgGen"
description = "Generates a receipt image"
inputs = { receipt_prompt = "ReceiptPrompt" }
output = "Image"
prompt = "$receipt_prompt"
model = "@default-small"

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
html_report = { from = "html_report",  }
