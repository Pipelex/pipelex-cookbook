# A method as a CrewAI agent's tool

An agent framework is good at deciding what to do next and poor at doing one thing the same way every time. This recipe gives a CrewAI crew a Pipelex method as a tool, so the part that must be repeatable comes out of a fixed pipeline with a typed result, and the crew keeps its freedom around it.

The crew has two agents:

- **The reviewer** calls `review_nda`, a CrewAI tool that runs the cookbook's [NDA review](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/review_nda) method by its address on a counterparty's NDA, against the company's NDA playbook, and returns the review as JSON: a verdict, a note for counsel, and one row per position of the playbook with the clause found, the assessment and the playbook's fallback wording, validated by the `NdaReview` model generated from the method. The playbook is the company's and does not change from one NDA to the next, so the tool holds it, and the agent names only the NDA.
- **The editor** explains the review in plain language to the colleague who needs the NDA signed: what it means, whether the NDA can be signed now, and what to do next. It writes no verdict and no contract wording of its own, since the script copies those into the memo from the review itself.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them, including CrewAI.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). The tool's call is one run on the hosted API and spends credit.
- A model for the crew's own agents. CrewAI uses OpenAI unless told otherwise, so set `OPENAI_API_KEY`, or set `MODEL` and that provider's key as [CrewAI's documentation](https://docs.crewai.com/en/concepts/llms) describes.

## Run it

```bash
export PIPELEX_API_KEY=… OPENAI_API_KEY=…
uv run crew.py
```

With no argument, the crew reviews the method's sample: Common Paper's Mutual NDA, its cover page completed for the example as a counterparty's draft, against a playbook written for the example. For your own NDA, give its link, which the hosted API must be able to fetch, and your playbook as a text or Markdown file:

```bash
uv run crew.py https://example.com/their-nda.pdf --playbook our-nda-playbook.md
```

## What you get

The memo, printed and saved to `memo.md`: the review's verdict, the editor's explanation, then every position the review does not find acceptable, with what the draft says and what the playbook asks for, and the note for counsel. The review comes from one run, whose id the tool prints on the terminal.

On the sample NDA, the review found the confidentiality period, set to last in perpetuity, one to negotiate, and the non-solicitation clause the cover page adds one to refuse, and sent the draft to counsel. The memo, one page:

```markdown
# NDA review

**Verdict:** Escalate to counsel

The review says that this mutual NDA is mostly fine, but it cannot be signed as it is now because of two key issues. …

Because these points involve specific company policies and legal principles, the review recommends escalating this NDA to our legal counsel to handle those changes properly. You should not sign this NDA yet. …

## What to ask for

### Confidentiality period: to negotiate

**The draft says** (Cover Page, Term of Confidentiality): The Cover Page selects "In perpetuity" for the Term of Confidentiality. …

**The playbook asks for:**

> Five years from the Effective Date, but in the case of trade secrets until the information is no longer a trade secret under applicable law.

### Non-solicitation, non-competition and exclusivity: to refuse

**The draft says** (Cover Page, MNDA Modifications): It adds a non-solicitation restriction: “During the MNDA Term and for twelve (12) months after it ends, neither party will directly or indirectly solicit for employment” certain employees of the other party.

**The playbook asks for:**

> delete the clause.

## Note for counsel

> This is a mutual Common Paper MNDA governed by Delaware law, with a perpetual confidentiality term selected on the Cover Page. It cannot be signed as drafted because the Cover Page adds a non-solicitation restriction, which the playbook requires deleting from an NDA; …
```

The explanation is the editor's, written by CrewAI's model, and reads differently from one run to the next. The verdict, what the draft says, the playbook's wording and the note for counsel are the review's, character for character.

## How it is built

- `crew.py` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/review_nda@v0.20.0`, pinned to a release tag so the method never changes under the types. It gives the NDA as a document by its link, and the playbook as the method's `NdaPlaybook`; with no `--playbook`, it reads the sample playbook from the method's `inputs.json` at that release.
- `generated/review_nda/` holds the method's types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- The crew keeps its freedom to decide and to explain, while the decision, the wording and the escalation come from the method's typed result. An agent that retells a review can reword the playbook's fallback, leave out what goes to counsel or misstate whether the NDA can be signed, and those are the parts someone signs on, so no agent writes them: the tool keeps the `NdaReview` it returned, and `render_memo` writes the verdict, the positions to change and the note for counsel from it, around the editor's explanation. The tool's JSON is the reviewer's answer as it stands (`result_as_answer`), so the editor explains the very review the memo is rendered from. When the crew finishes without the tool having returned a review, the script stops and writes no memo.
- The tool is an ordinary `BaseTool` whose `_run` waits for the run, so any other framework that takes a Python function as a tool takes the same `review_nda` coroutine.
