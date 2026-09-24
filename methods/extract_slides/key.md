# Key: catops_deck

Inputs: `assets/presentations/CatOps.pdf`, a twelve-slide parody pitch deck for "CatOps", a platform for managing cat interruptions in remote work, in landscape slides mixing text boxes, photographs and charts. It is the sample the example has always shipped with, shared with the cookbook's other slide examples.

## Planted facts
F1. The deck has twelve slides, titled in order: CatOps (the title slide, with the tagline "Operational Excellence for Feline Stakeholders" and the footnote "Parody / Synthetic deck for demo purposes"); Remote Work Has a Hidden Operational Crisis; Current Solutions Don't Scale to Enterprise Needs; CatOps Delivers End-to-End Incident Management; Enterprise-Grade Modules for Complete Cat Operations; Intelligent Workflow Reduces Response Time by 84%; $47B Addressable Market in Remote Work Infrastructure; Flexible Pricing Scales from Solopreneurs to Enterprises; Early Traction Validates Product-Market Fit; Multi-Channel Strategy Targets Remote Work Ecosystem; Product Roadmap Expands Platform Capabilities; Experienced Team Seeking Strategic Partners.
F2. Slide 2 gives 73% of remote workers, 47 Minutes lost per incident, a 3.2x increase in meeting duration and $12.3 Billion of annual cost, and shows a photograph of a tabby cat chewing a frayed cable beside a "NEVER AGAIN" sticky note.
F3. On slide 2 and slide 4 the bullet labels are drawn over the sentences they introduce, so the rendering overlaps and the PDF text layer scrambles slide 4 into "Real Keyboard pressure & webcam motion sensors (0.3s latency). -time Monitoring:". The intended bullets are, on slide 2, Keyboard Takeovers, Cable Sabotage and Current Strategy, and on slide 4, Real-time Monitoring, Severity Scoring, Automated Response and Predictive Analysis.
F4. Slide 3 holds a horizontal bar chart, "Failure Rates of Traditional Methods", over six methods: "Hope" Strategy, Closing the Door, Bribery (Treats), Reactive Scritching, Decoy Keyboard and Spray Bottle (Legacy).
F5. Slide 4 holds a donut chart, "Incident Outcome Distribution", with four categories: Proactively Prevented, Auto-Resolved (Treats), Auto-Resolved (Laser) and Human Intervention Required.
F6. Slide 6 draws a six-step workflow as two rows of numbered boxes, 1 to 3 left to right on top and 4 to 6 right to left underneath, so reading the boxes row by row gives 1, 2, 3, 6, 5, 4. The steps are 1 Event Intake, 2 Severity Scoring, 3 Playbook Selection, 4 Automated Response, 5 Verification and 6 Meowtem Generation, and the slide says response time fell from 8.4 minutes to 1.3 minutes.
F7. Slide 12's four team portraits did not render: each circle shows only the broken image's alternative text, the person's name.

## Must
M1. `text` holds twelve sections, one per slide and in the deck's order, each opening with a level-one heading that gives the slide's own title or a close paraphrase of it, from "CatOps" for the title slide to "Experienced Team Seeking Strategic Partners" for the last.
M2. Every section carries, after a `**Description:**` label, a description of that slide's layout and graphics.
M3. The section on the remote work crisis gives its four figures: 73% of remote workers, 47 minutes lost per incident, a 3.2x increase in meeting duration and $12.3 billion of annual cost to enterprises.
M4. The section on the remote work crisis describes the photograph of a cat chewing a cable.
M5. The section on the remote work crisis gives its three bullets as readable sentences: keyboard takeovers occur most frequently during deadline-sensitive work, 89% of cable sabotage incidents happen during investor calls, and the current strategy of "Hope" and "Closing Doors" is failing at scale.
M6. The section on incident management gives its four bullets as readable sentences, each with its label: Real-time Monitoring (keyboard pressure and webcam motion sensors, 0.3s latency), Severity Scoring (P0 Critical to P4 Info based on meeting context), Automated Response (treats, lasers or calming audio) and Predictive Analysis (forecasting high-risk periods).
M7. The section on incident management names the donut chart of incident outcomes and its four categories: Proactively Prevented, Auto-Resolved (Treats), Auto-Resolved (Laser) and Human Intervention Required.
M8. The section on failing current solutions names the bar chart of failure rates and at least four of its six methods: "Hope" Strategy, Closing the Door, Bribery (Treats), Reactive Scritching, Decoy Keyboard and Spray Bottle (Legacy).
M9. The section on enterprise modules names the six modules: Incident Console, Purrformance Dashboard, Treat Orchestrator, Cat-Access Control, Playbook Library and Meowtem Analysis.
M10. The section on the intelligent workflow gives the six steps with their own numbers, or listed in their numbered order: 1 Event Intake, 2 Severity Scoring, 3 Playbook Selection, 4 Automated Response, 5 Verification, 6 Meowtem Generation.
M11. The section on the intelligent workflow says average response time fell from 8.4 minutes to 1.3 minutes.
M12. The section on the addressable market gives TAM $47 billion, SAM $14.1 billion, SOM $1.4 billion and Expansion $89 billion.
M13. The section on pricing gives the tiers Free (1 cat), Pro at $29 a month and Enterprise at a custom price, and the add-ons at $99 and $199 a month.
M14. The section on early traction gives $2.1M ARR, 847k paws per quarter, 12,300 incidents resolved, a 67% reduction in disruptions and 4.8/5.0 customer satisfaction.
M15. The section on the product roadmap lists its five items with their quarters: Zoom Background Auto-Cat Blur in Q2 '26, Predictive Cable Risk Analysis in Q3 '26, Multi-Pet Conflict Resolution in Q4 '26, Litterbox Telemetry (v2) in Q1 '27 and DogOps Integration in Q2 '27.
M16. The section on the team gives the $8M Series A ask and the four team members with their roles: Sarah Chen, CEO & Co-Founder; Dr. Marcus Williams, Chief Feline Officer; Priya Patel, CTO; James Rodriguez, Head of Growth.

## Must not
N1. An HTML comment such as `<!-- PageHeader=… -->`, `<!-- PageFooter=… -->` or `<!-- PageNumber=… -->` left in `text`.
N2. A bullet whose label and sentence are run together or scrambled as the PDF's text layer has them, such as "Real Keyboard pressure & webcam motion sensors (0.3s latency). -time Monitoring".
N3. A figure that differs from the slide's, such as billions read as millions, the 3.2x increase given as a percentage, or $47B given as $47M.
N4. A slide missing, two slides merged into one section, or a slide given two sections.
N5. A workflow step given another step's number, such as Meowtem Generation numbered 4 because it sits fourth when the boxes are read row by row.
N6. A description of the team slide that describes the team members' faces or appearance: their portraits did not render.

## Also acceptable
A1. The title slide headed "CatOps" alone or with its tagline, "CatOps: Operational Excellence for Feline Stakeholders", for M1.
A2. The description set as a blockquote or as a plain paragraph after its label, for M2.
A3. The team portraits described as broken images, empty circles or placeholders showing the names, or not mentioned at all, for N6.

## Pass bar
Every Must and Must not line.
