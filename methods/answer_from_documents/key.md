# Key: pew_latino_economy_references

Inputs: one document, Pew Research Center's report "Latinos Increasingly Confident in Personal Finances, See Better Economic Times Ahead" (Lopez, Morin and Krogstad, June 8, 2016), a 23-page PDF hosted on Hugging Face as part of the MMLongBench-Doc benchmark, with the question "Among all 12 references in this report, how many are from its own research center?" and no context. It is the sample the example has always shipped with.

## Planted facts
F1. The report is Pew Research Center's: its cover gives the recommended citation "Washington, D.C.: Pew Research Center", and every page carries the "PEW RESEARCH CENTER" header.
F2. Appendix A: References, on printed pages 21 and 22 (PDF pages 22 and 23), lists twelve references.
F3. Eight of them are Pew Research Center publications: Kochhar 2014; Kochhar and Fry 2014; Kochhar, Fry and Taylor 2011; Lopez, Gonzalez-Barrera and Krogstad 2014; Pew Research Center 2015; Pew Research Center 2014; Pew Research Center 2009; and Stepler and Brown 2016.
F4. Three of the eight name "Pew Research Center" as their author; the five others are by named Pew researchers and give "Washington, D.C.: Pew Research Center" as publisher. In the Lopez, Gonzalez-Barrera and Krogstad entry, "Pew Research Center" is split across a line break.
F5. The four others come from elsewhere: Blumberg and Luke 2016 (National Center for Health Statistics), DeNavas-Walt and Proctor 2015 (U.S. Census Bureau), National Bureau of Economic Research 2010, and Weeks 2014 (Selig Center for Economic Growth).

## Must
M1. `status` is `answered`.
M2. `answer` is 8.
M3. `supporting_passages` holds at least one quote from the report's Appendix A: References, and every quote's words appear in the report in the same order, allowing for differences in line breaks, spacing and quote characters that come from the text extraction.
M4. `explanation` or `supporting_passages` names Pew Research Center as the report's own research center.
M5. `confidence` is `high` or `medium`.

## Must not
N1. `answer` is 3, counting only the references whose author is "Pew Research Center" and missing the five by named Pew researchers.
N2. `answer` is 7, missing the Lopez, Gonzalez-Barrera and Krogstad 2014 reference, whose "Pew Research Center" is split across two lines.
N3. `answer` above 8, counting a reference published by the National Center for Health Statistics, the U.S. Census Bureau, the National Bureau of Economic Research or the Selig Center for Economic Growth.
N4. A quote in `supporting_passages` that is paraphrased or invented rather than copied from the report.
N5. `status` an abstention, with `answer` set to "Not answerable".

## Also acceptable
A1. `answer` written "8 references" rather than the bare number, for M2.
A2. A passage's `page_number` given as the printed page (21 or 22) or as the PDF page (22 or 23), for M3.

## Pass bar
Every Must and Must not line.
