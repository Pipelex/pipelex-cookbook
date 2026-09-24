# Key: two_employees

Inputs: `nb_employees`, 2. The method takes nothing else: every fact below is a rule the method imposes on what it generates, which the output must respect. The example used to ask for ten employees; two show the same mix at a fifth of the image generations.

## Planted facts
F1. `nb_employees` asks for two employees of a tech company whose email domain is acmecorp.com, in the departments Engineering, Marketing, Sales, Finance or Product.
F2. Each employee gets three or four expenses. Every set holds one legitimate expense and one weekend expense; a set of three adds one inflated amount, receipt mismatch or vague purpose; a set of four adds one receipt mismatch and one vague purpose or inflated amount.
F3. The expenses are dated in January 2026. Its weekend days are the 3rd, 4th, 10th, 11th, 17th, 18th, 24th, 25th and 31st, with Sunday 1 February closing the last weekend; a weekend expense takes one of those dates, and the other expenses take weekdays.
F4. A receipt mismatch is bought at a personal or entertainment business (bowling alley, streaming service, gaming store, movie theater, spa, gym, liquor store or nightclub) and claimed with a business-sounding purpose.
F5. Every amount is in USD, with an 8% tax on the receipt.

## Must
M1. The output lists exactly two employee reports, and their two `employee.employee_id` values differ.
M2. Each `employee` fills every field: `employee_id` is "EMP-" followed by digits, `full_name`, `email`, `department`, `job_title`, and a `seniority` that agrees with the job title (a "Senior Engineer" is Senior, a "VP of Sales" is VP).
M3. Each `employee.email` is the employee's first and last name at acmecorp.com, as firstname.lastname@acmecorp.com, case and accents aside, and each `department` is Engineering, Marketing, Sales, Finance or Product.
M4. Each report's `expenses_with_receipts` holds three or four expenses.
M5. In each report, exactly one expense has `scenario.scenario_type` "legitimate" and exactly one has "weekend_expense"; a report with four expenses also has exactly one "receipt_mismatch".
M6. Every `expense.expense_date` falls in January 2026, or on Sunday 1 February 2026 for a weekend expense.
M7. Each weekend expense's `expense_date` is a Saturday or a Sunday and equals its `scenario.target_date`.
M8. Every `expense.currency` is "USD", and every `expense.total_amount` is positive with at most two decimals.
M9. Every `expense.expense_id` is "EXP-", the expense date as YYYYMMDD, a hyphen and five digits, and its date part equals the expense's `expense_date`.
M10. A receipt-mismatch expense has a filled `scenario.fake_purpose`, and its `business_purpose` claims a business reason (the fake purpose or a rewording of it); its receipt image shows a purchase at a personal or entertainment business.
M11. A vague-purpose expense has a `business_purpose` that names no specific business need, such as "Business expense", "Work related" or "Misc".
M12. An inflated-amount expense has a `scenario.amount_multiplier` of 2 or more.
M13. Every expense's `receipt.public_url` opens as an image of a printed receipt, headed by a merchant name and showing a legible total.
M14. Every legible total on a receipt image equals its expense's `expense.total_amount` within 0.01.
M15. Each `html_report.inner_html` names the employee's `full_name` and has one table row per expense, giving its `expense_id`, its date, its `business_purpose`, its amount and its receipt image by the receipt's `public_url`.

## Must not
N1. A legitimate expense dated on a Saturday or a Sunday.
N2. A weekend expense dated on a weekday.
N3. Two expenses anywhere in the dataset with the same `expense_id`.
N4. A `business_purpose` that gives the label away: naming the fraud, the scenario type, or admitting the purchase was personal or unapproved.
N5. The scenario label (legitimate, weekend expense, inflated amount, receipt mismatch, vague purpose) printed in an `html_report`, which stands for what the employee submits.

## Also acceptable
A1. A weekend expense whose `business_purpose` names the weekend day ("Urgent client meeting on Saturday"), for N4: it states when, not that the expense broke a rule.
A2. A `scenario.target_date` filled for an expense that is not a weekend expense, as long as it is a weekday, for M7 and N1.

## Pass bar
Every Must and Must not line, except that M13 may be partial for one receipt image in the whole dataset whose total is blurred or cropped: that is the image model's rendering, not the method's data. M14 holds for every total that can be read.
