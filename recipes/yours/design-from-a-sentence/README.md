# A method designed from a sentence and proven by a lab

When no published method does what you need, your coding agent designs one from a sentence of yours, then proves it the way a lab would: it writes down what a right answer is before anything runs, makes test documents with facts planted in them, runs the method on them within a budget you agree, scores every run against its key, and fixes the method until each case passes. This recipe does it for a method that reads a CV against a job offer and prepares five questions for the interview, and shows what the lab found: a first version that passed one case and failed the other on one line, one fix, and a second round in which both passed, for $0.18.

It shows what designing a method involves today:

- **A sentence is enough to start.** `/pipelex-design` turns it into a method of five steps, with the concepts it reads and returns, and validates it before handing it over.
- **The key comes before the run.** `/pipelex-lab` writes each test case's answer key, with its planted facts and the lines a right answer must and must not hold, before the first run, so a run is scored against what you decided was right, never against what the method happened to say.
- **A trap is what finds the fault.** A clean case shows that the method works; a case built to mislead it, here a CV whose summary claims more than its roles show, shows where it doesn't.
- **Spending waits for your go.** The lab proposes a budget from its estimate of a round's cost and runs nothing until you agree to it, and it stops before a run the budget does not cover.

## What it needs

- Claude Code or Codex with the Pipelex plugin and your Pipelex API key, set up as the plugin's [quick start](https://github.com/Pipelex/pipelex-plugins#quick-start) says, started in the directory the method goes into: the plugin's tools read and write files in the directory your agent was started in.
- `uv`, or Python 3 with `venv`, which `/pipelex-synthetic-inputs` uses to render the test documents with Python code on your machine.
- Credit on your Pipelex account: each run of the method is one run on the hosted API, and the lab's budget bounds how many it starts. Designing, validating, editing and making the test documents spend none.

## Run it

In an empty directory, ask your agent:

> Design a method that takes a CV and a job offer, both PDFs, analyzes whether they match, and generates 5 questions for the interview. Then prove it with /pipelex-lab.

The agent designs the method, then the lab frames the experiment and stops to show you its answer keys, the budget it proposes and what a round will cost. Correct a key there if it is wrong, and give your go with the budget you accept: the lab proposed $2 here, and the go allowed up to $5. From then on it runs, scores, logs and fixes by itself, and ends on a scorecard.

## What you get

`/pipelex-design` wrote `methods/cv_job_match/main.mthds`, valid and runnable at its first validation. Its main pipe, `match_cv_to_job_offer`, reads the two documents' pages, has `analyze_match` judge the CV against each of the offer's requirements, has `write_interview_questions` write exactly five questions from that analysis, and returns them together as an `InterviewPrep`:

```text
InterviewPrep
  analysis: MatchAnalysis    candidate_name, job_title, verdict (strong_match, partial_match or weak_match), match_score,
                             summary, matching_strengths, gaps, points_to_verify
  questions: InterviewQuestion[5]    question, focus (gap, strength, verification or motivation), purpose
```

`/pipelex-lab` wrote its brief in `lab/cv_job_match/brief.md`: what a right output gets right, such as years in a skill counted from the dates of the roles that use it and never from the summary's headline figure, and the mistakes that cost the most, which become the traps of the cases. It set up two cases under `lab/cv_job_match/cases/`, each with its inputs and its `key.md`:

- `clean-strong-match`, a CV that meets every must-have requirement of the offer, which the method must call a strong match.
- `trap-overstated-cv`, a CV whose summary says "8 years of experience" and "Expert in Python, Kafka and Kubernetes", while its only Python role lasted 3 years and 8 months, no role mentions Kafka or Kubernetes, its German is B1 where the offer asks for C1, and 18 months are missing between two roles.

`/pipelex-synthetic-inputs` rendered the CVs and the offer as PDFs with those facts in them, on your machine and for nothing, and `/pipelex-inputs` uploaded them. The trap's key holds lines such as these:

```text
M4. `analysis.gaps` names the Python requirement as unmet, counting the Python experience as 3 to 4 years, or as since January 2023, against the 5 required.
M6. `analysis.points_to_verify` names the gap between June 2021 and January 2023, in any wording that gives those dates, or a length of 17 to 19 months or about a year and a half.
N1. `analysis.verdict` is `strong_match`.
N4. `analysis.matching_strengths` credits Kafka or Kubernetes as met without saying that no role shows them.
```

The first round passed the clean case and failed the trap on one line, as the log in `lab/cv_job_match/log.md` records:

```text
### run_aacb6f9c-bb51-4aca-b4b7-4f37e1d60cec · trap-overstated-cv
$0.045 · 27 s · 18 of 19 lines · pass bar met: no
Failed: N4 (`analysis.matching_strengths` holds "Nice-to-have — Kafka and Kubernetes: both are listed in the summary/skills, with the summary calling her an expert in Kafka and Kubernetes.", crediting the summary's own claim with no caveat in that field, while `gaps` and `points_to_verify` call both unsupported by any role).
```

The method had counted the Python years right, caught the missing months and refused the strong match, but it took the summary's word for Kafka and Kubernetes. The lab read the failure as the method's, since the input shows no role using either, and had `/pipelex-edit` add two rules to `analyze_match`'s prompt:

```diff
 - A requirement is met only when the CV states concrete evidence for it (a role, a project, a degree, a certification, a number of years). Name that evidence.
+- The candidate's own summary, profile or skills list is a claim, not evidence. A skill that appears only there, with no role, project, degree or certification showing it in use, does not meet a requirement: put that requirement in gaps as claimed but not demonstrated, and add the claim to points_to_verify. Never put it in matching_strengths.
+- Each requirement goes in exactly one of matching_strengths or gaps, never in both.
```

The second round passed both cases, with no line that had passed before failing, and the lab stopped there:

```text
## Scorecard · series 1
- clean-strong-match: 16 of 16 lines, pass bar met. Nothing failing.
- trap-overstated-cv: 19 of 19 lines, pass bar met. Nothing failing.
- Rounds: 2. Spent: $0.177 of the $2.00 budget ($0.043 + $0.045 in round 1, $0.045 + $0.044 in round 2). Total over the whole log: $0.177.
- Stop: every case meets its pass bar (stop 1), in round 2, after one fix to analyze_match.
```

Two cases passing prove the method on those two cases. The lab's next step names what would prove more: a harder case, such as a CV in another language, a two-page CV or a borderline verdict. Once you trust the method, save it to your catalog with `/pipelex-catalog` and point your chatbot, your code and your app at its id, as the [copy-and-change recipe](../copy-and-change/) does.

## How it is built

The recipe is a request to your agent, so it carries no code: the Pipelex plugin's skills do the work through the Pipelex tools, and `/pipelex-lab` calls the others.

- **The design.** [`/pipelex-design`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-design/SKILL.md) turns the sentence into the concepts and pipes of a `.mthds` file, and validates it with `mthds_validate` until it is valid and runnable.
- **The experiment.** [`/pipelex-lab`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-lab/SKILL.md) writes the brief, the cases and their keys under `lab/<method>/`, proposes the budget, and stops for your go. Its log records every run with its cost, its score and the lines it failed, and ends each series on a scorecard; a log already there is continued, never restarted. When the directory is a git repository, the log names the commit each series started from, so that a fix can be undone; the proof of this recipe ran outside one, and the lab kept a copy of the method as it was instead.
- **The test documents.** [`/pipelex-synthetic-inputs`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-synthetic-inputs/SKILL.md) renders them with Python code on your machine and never with a model, and [`/pipelex-inputs`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-inputs/SKILL.md) uploads them and writes each case's `inputs.json`. Your own documents can take their place: the lab keeps a case of your own files out of version control.
- **The runs and the fix.** [`/pipelex-run`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-run/SKILL.md) starts each run from the method's files, and [`/pipelex-edit`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-edit/SKILL.md) makes each fix that keeps what the method takes and returns, validating the method before and after.
