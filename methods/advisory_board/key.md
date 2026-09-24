# Key: saas_churn

Inputs: `user_input`, inline in `inputs.json`, a business problem told in a few paragraphs: a mid-stage B2B SaaS company whose customer churn has nearly doubled, asking how to spend a fixed budget to bring it back down. It is the problem the example has always shipped with.

## Planted facts
F1. The company is a mid-stage B2B SaaS business with 50 employees and $5M of annual recurring revenue.
F2. Annual churn has risen from 8% to 15% over the past six months.
F3. Onboarding takes 4 to 6 weeks against an industry average of 2 to 3 weeks, support answers in 24 hours on average, only 30% of customers use the advanced features, and three new competitors offer a better user experience.
F4. The goal is churn under 10% within six months, while keeping the growth targets.
F5. The budget is $500K.
F6. The team counts 8 engineers, 4 salespeople, 3 marketers, 2 customer-success staff and 5 in operations.
F7. The stakeholders are the CEO, the VP Product, the VP Sales and the Head of Customer Success.
F8. The method offers sixteen advisory boards and asks for five to ten of them to be consulted.

## Must
M1. The output is one Markdown document organised under headings, starting directly with the report.
M2. The report opens with an executive summary.
M3. The report restates the problem with its figures: annual churn up from 8% to 15%, and the goal of bringing it under 10% within six months.
M4. The report lists the boards consulted, between five and ten of them, each one of the sixteen the method offers: Executive Leadership, Product Management, GTM, Engineering & Technology, Operation & Infra, Supply Chain & Procurement, Marketing & Communication, Sales & Business Operation, Growth Consulting, Customer Success & Support, Finance & Corporate Development, HR & People, Design & UX, Data Science & Analytics, Legal & Compliance, and Security & Risk Management (in any close wording, with or without "Advisory Board").
M5. The Customer Success & Support board is among the boards consulted.
M6. The report names its top three consensus recommendations.
M7. At least one recommendation targets onboarding, which the problem puts at 4 to 6 weeks against an industry average of 2 to 3 weeks.
M8. At least one recommendation targets the 24-hour support response time or the 30% adoption of advanced features.
M9. The consensus recommendations each name the boards supporting them and a confidence score or priority.
M10. The report sets out at least one strategic choice where boards disagree, giving each side's position, the core tension and a way to decide.
M11. The report gives insights by domain or functional area.
M12. The implementation roadmap has three phases, covering the first 30 days, one to three months, and beyond three months (in any close wording), each with actions and who leads them.
M13. The risk assessment lists risks each with a severity (high, medium or low), a mitigation and an owner.
M14. The resource requirements name the budget the plan spends, together with the people or technology it needs.
M15. The success metrics include churn, with a target under 10% within six months, and say how and how often each metric is measured.
M16. The report ends with next steps and a review schedule.

## Must not
N1. The document wrapped in a Markdown code fence, or preceded or followed by a sentence addressed to the reader about the formatting.
N2. A board consulted that is not one of the sixteen the method offers.
N3. Resource requirements whose total spend exceeds the $500K budget, or a plan premised on a larger budget.
N4. The churn figures misstated: a current rate other than 15%, a former rate other than 8%, or a target other than under 10% within six months.
N5. The company described otherwise than as a B2B SaaS business with 50 employees and $5M of annual recurring revenue.
N6. A section left empty or holding a placeholder such as "TBD".

## Also acceptable
A1. Sections in another order or under other headings, as long as each is recognisable, for M2 to M16.
A2. Tables rather than bullet lists for the recommendations, the roadmap, the risks, the resources or the metrics, for M9 and M12 to M15.
A3. The roadmap's later phases stretched to six months to match the goal's horizon, as long as there are three phases starting with the first 30 days, for M12.

## Pass bar
Every Must and Must not line.
