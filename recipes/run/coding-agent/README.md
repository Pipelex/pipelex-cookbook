# A run in your coding agent, followed later by its id

A run does not need anyone to wait for it. In Claude Code or Codex with the Pipelex plugin, you ask for a run in a sentence: `/pipelex-run` checks the method at its address, starts the run and gives you its id at once. The run carries on server-side, and from any later session, in any directory, the id alone is enough for your agent to tell you how the run is going, show you its results and save them. This recipe does it with the cookbook's [document question answering](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/answer_from_documents) method, on its sample: the European Commission's guidelines on the definition of an AI system under the AI Act, and a question a customer support team asks about a tool of its own. The method answers from the documents it is given, quoting the passages its answer rests on with their pages.

It shows what the agent does with a published method:

- **An address is a complete run source.** The agent passes `github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0` as it is, and nothing is cloned or installed. The run reports its provenance: the address, the tag and the commit the tag resolved to.
- **Nothing is spent before the method is proven.** The agent validates the method at its address before it starts the run, and "do a dry run first" stops there: it reports what the method takes and returns, says that no model ran, and waits for your go.
- **An id is all it takes to come back.** In a new session, days later, asking how the run is going, for its results or to save it needs nothing else, and saving writes the run to `runs/<run_id>/` under the directory the agent was started in.

## What it needs

- Claude Code or Codex with the Pipelex plugin and your Pipelex API key, set up as the plugin's [quick start](https://github.com/Pipelex/pipelex-plugins#quick-start) says. If the Pipelex MCP is also on your Claude account, turn it off in Claude Code with `/mcp`, as the quick start explains.
- Credit on your Pipelex account: the answer is one run on the hosted API and spends credit, while following it, reading its results and saving them spend none.

## Run it

In a directory of your choice, ask your agent:

> Run github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0 on https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/assets/answer_from_documents/ai_system_definition_guidelines.pdf with the question: Our customer support team wants each new ticket to show an expected resolution time, computed as the average resolution time of past tickets in the same category. Is that tool an AI system under the AI Act?

The agent picks `/pipelex-run` for the request, and you can also name the skill yourself. It says in one line what is about to run and that it spends credit, starts the run, and reports the run's id first. Let it follow the run to the end, or close the session: the run does not depend on it.

Later, from any session and any directory, with a key of the same account:

> How is run run_… going?
>
> Get the results of run run_…
>
> Save run run_…

To see what would run before anything is spent, ask for a dry run first:

> Do a dry run first, then run github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0 on https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/assets/answer_from_documents/ai_system_definition_guidelines.pdf with the question: Our customer support team wants each new ticket to show an expected resolution time, computed as the average resolution time of past tickets in the same category. Is that tool an AI system under the AI Act?

The agent validates the method, reports what it takes and returns, and ends its turn there: the run starts only once you say so.

## What you get

The agent says what it is about to run, then reports the run's id and where the method came from:

```text
The method validates at v0.20.0. Running github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0 (main pipe document_qa.answer_from_documents). Both inputs come from your request: the PDF URL as documents and your question as question. I left the optional context input empty. This spends inference credit.

Run started: run_…. The address resolved at tag v0.20.0 to commit aeee4835f56ace0eada10dc4b2ed8780b0473111, so that is exactly what runs.
```

Left to follow the run, it reported the answer when the run completed, about 75 seconds later, for $0.40 across 5 model calls. From a second session, in another directory, asked how the run is going and then for its results:

```text
> How is run run_… going?

Run run_… has finished with status COMPLETED. It started at 08:02:30 UTC today and ended at 08:03:45 UTC, so it ran for about a minute and a quarter.

If you'd like, I can fetch its output or save its files to disk.

> Get the results of run run_…

Here are the results of run run_…. The method answered with "No", at high confidence.

Explanation: Suppose the tool does only what is described: it applies a fixed arithmetic-mean rule to past tickets in the same category. The Commission Guidelines treat that as a static estimation or basic statistical system, not as an AI system. They even use a customer-support system that predicts mean resolution time from past data as one of their baseline examples. They also say that a system whose performance a basic statistical learning rule can achieve falls outside the AI-system definition. The answer could change if the implementation learns the ticket categories, derives a model or algorithm from data, or uses more sophisticated inference than taking the mean.

Supporting passages. All come from the Commission Guidelines on the definition of an AI system, C(2025) 5053 final:
- p. 2, Art. 3(1): the definition that the tool is assessed against.
- p. 5, ¶26: the capability to infer is indispensable, and software that only executes rules defined by people is excluded.
- p. 9, ¶46: fixed-rule processing without learning, reasoning or modelling is basic data processing. One of its examples is software that calculates a population average.
…
- p. 10, ¶51: this is the closest match. It names a "customer support response time system … based on static estimation to predict the mean resolution time from the past data" as an example.
…
- p. 1, ¶7: the Guidelines are not binding, and only the CJEU can give an authoritative interpretation.

Contradictions noted: none.

Caveats: The answer assumes the categories are set manually or by fixed rules, and that the displayed time is the plain arithmetic average. Learned categorisation, weighting, regression or model-based prediction could change the classification. The Guidelines themselves are not binding.

The run cost $0.40 across 5 model calls.

The output hasn't been saved to disk. If you want a local copy, I can save the run.
```

The answer is right: under "Simple prediction systems", on the page the guidelines number 10, paragraph 49 places outside the definition the systems a basic statistical rule can match, and paragraph 51 gives as an example a customer support system predicting the mean resolution time from past data. The output is the method's `DocumentAnswer`: its status, the answer, the explanation, each supporting passage with its document and page, the contradictions noted between documents, the caveats and a confidence.

Saving the run writes its whole output as `runs/<run_id>/main_stuff.json` under the directory the agent was started in, and reports the path:

```text
> Save run run_…

I saved run run_… to:

…/runs/run_…/main_stuff.json (10.5 KiB)

That file is the whole run: it holds the main output exactly as the API returned it. The output doesn't point to any stored files, so there was nothing else to download.
```

## How it is built

The recipe is a request to your agent, so it carries no code: the plugin's [`/pipelex-run`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-run/SKILL.md) skill does the work through the Pipelex tools.

- **The inputs.** The agent takes the address as the method's `method_ref`, reads the document's link and the question from your request, and checks them against the method's input template (`mthds_inputs_template`). Had you not given them, it would look for the method's inputs in `./answer_from_documents/`, the directory named after the address, where `/pipelex-inputs` writes them.
- **The proof.** `mthds_validate` validates the method at its address before any credit is spent, and a dry run ends there. A published method that fails validation is reported with its address and its tag, and is not yours to repair: another tag, or its publisher, is the fix.
- **The run.** `mthds_run` starts it and returns its id at once, with its `method_provenance`. `mthds_run_status` follows it, waiting as long as the API asks between two readings, and a status marked `degraded` is read as the last one known, never as a stuck or failed run.
- **The results.** `mthds_run_results` reads the output of a run that has ended, and `mthds_download_artifacts` saves it, days after the run as well. Before saving into a git repository, the agent makes sure `runs/` is ignored, adding it to `.gitignore` when it is not, and says so.
- **The address is pinned** to a release tag, so the run executes the method as it was at that release. An address without a tag runs whatever its default branch holds at the moment, and the agent says so in one line.
- The same lifecycle, without an agent: the [HTTP recipe](../http/) makes the three calls with `curl`, and the [durable run](../../code/typescript/durable-run/) recipe makes them with the TypeScript SDK.
