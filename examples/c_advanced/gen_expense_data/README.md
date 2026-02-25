# Synthetic Expense Data Generation

This example demonstrates generating synthetic expense reimbursement data with receipt images and HTML reports.

## Overview

The pipeline generates complete expense reports for multiple employees, including:
- Employee profiles
- Multiple expenses per employee (2-5, determined by LLM)
- AI-generated receipt images for each expense
- HTML expense report document

## Pipeline Architecture

```
generate_expense_dataset (PipeSequence)
├── generate_employees (PipeLLM) → Employee[]
└── generate_employee_report (PipeSequence, batch_over employees)
    ├── generate_expenses (PipeLLM) → Expense[]
    ├── generate_expense_with_receipt (PipeSequence, batch_over expenses)
    │   ├── generate_receipt_prompt (PipeLLM) → ReceiptPrompt
    │   ├── render_receipt (PipeImgGen) → Image
    │   └── compose_expense_with_receipt (PipeCompose) → ExpenseWithReceipt
    └── render_expense_report_html (PipeCompose) → Html
```

## Data Structures

### Employee
- `employee_id`: Unique identifier (EMP-XXXX format)
- `full_name`: Employee name
- `email`: Email address
- `department`: Engineering, Marketing, Sales, Finance, Product
- `job_title`: Job title

### Expense
- `expense_id`: Unique identifier (EXP-YYYYMMDD-XXXX format)
- `expense_date`: Date of the expense
- `total_amount`: Amount in USD
- `currency`: Currency code
- `business_purpose`: Business justification

### Output
- HTML expense report with employee info, expense table, and receipt images

## Running the Example

```bash
# Validate the pipeline
pipelex validate examples/c_advanced/gen_expense_data/bundle.mthds

# Run with default inputs (5 employees)
pipelex run pipe examples/c_advanced/gen_expense_data/bundle.mthds \
  -i examples/c_advanced/gen_expense_data/inputs.json

# Run with custom number of employees
pipelex run pipe examples/c_advanced/gen_expense_data/bundle.mthds \
  -i examples/c_advanced/gen_expense_data/inputs.json \
  --override nb_employees.content.number=10
```

## Use Cases

- Testing expense validation systems
- Training ML models for expense categorization
- Demo data for expense management applications
- Load testing expense processing pipelines
