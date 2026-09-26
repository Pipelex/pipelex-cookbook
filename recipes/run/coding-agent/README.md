# A run in your coding agent, followed later by its id

A run does not need anyone to wait for it. In Claude Code or Codex with the Pipelex plugin, you ask for a run in a sentence: `/pipelex-run` checks the method at its address, starts the run and gives you its id at once. The run carries on server-side, and from any later session, in any directory, the id alone is enough for your agent to tell you how the run is going, show you its results and save them. This recipe does it with the cookbook's [research report](../../../methods/research_report/) method. It drafts a report from three angles out of the model's own knowledge, without searching any source, so what it returns is a first draft to check rather than verified research.

It shows what the agent does with a published method:

- **An address is a complete run source.** The agent passes `github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0` as it is, and nothing is cloned or installed. The run reports its provenance: the address, the tag and the commit the tag resolved to.
- **Nothing is spent before the method is proven.** The agent validates the method at its address before it starts the run, and "do a dry run first" stops there: it reports what the method takes and returns, says that no model ran, and waits for your go.
- **An id is all it takes to come back.** In a new session, days later, asking how the run is going, for its results or to save it needs nothing else, and saving writes the run to `runs/<run_id>/` under the directory the agent was started in.

## What it needs

- Claude Code or Codex with the Pipelex plugin and your Pipelex API key, set up as the plugin's [quick start](https://github.com/Pipelex/pipelex-plugins#quick-start) says. If the Pipelex MCP is also on your Claude account, turn it off in Claude Code with `/mcp`, as the quick start explains.
- Credit on your Pipelex account: the report is one run on the hosted API and spends credit, while following it, reading its results and saving them spend none.

## Run it

In a directory of your choice, ask your agent:

> Run github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0 on the question: what are the most promising approaches to improving battery energy density for electric vehicles?

The agent picks `/pipelex-run` for the request, and you can also name the skill yourself. It says in one line what is about to run and that it spends credit, starts the run, and reports the run's id first. Let it follow the run to the end, or close the session: the run does not depend on it.

Later, from any session and any directory, with a key of the same account:

> How is run run_… going?
>
> Get the results of run run_…
>
> Save run run_…

To see what would run before anything is spent, ask for a dry run first:

> Do a dry run first, then run github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0 on the question: what are the most promising approaches to improving battery energy density for electric vehicles?

The agent validates the method, reports what it takes and returns, and ends its turn there: the run starts only once you say so.

## What you get

When the run starts, the agent reports its id and where the method came from:

```text
Your run has started. Its id is run_…. Keep this id: it is how you follow the run from any later session.

The method came from github.com/Pipelex/pipelex-cookbook/research_report, tag v0.18.0, resolved commit 42dcaa9a5eafe62752ea8a5f7f57e5d83a2cca87.

Before any credit was spent, the method checked out as valid and runnable. The run spends inference credit.

What you can do next, from any session:
- Check progress: ask "how is run run_… going".
- Get the report when it is done: ask "get the results of run run_…".
- Save it to disk: ask to "save run run_…". That writes main_stuff.json and any files into runs/<run_id>/, and it still works days later.
```

From a second session, asked how the run is going and then for its results:

```text
> How is run run_… going?

Run run_… has completed. It was created at 03:48:59 UTC on 25 September 2026 and finished at 03:49:18 UTC, about 19 seconds later. This is a live status reading, not a last-known one. The results are ready whenever you want them.

> Get the results of run run_…

Run run_… completed, and its output is a research report on the most promising ways to improve battery energy density for electric vehicles. The run made 5 model calls and used 4,535 tokens.

In summary, the report takes a staged view. The nearest-term gains come from silicon-rich anodes and high-nickel cathodes, provided silicon expansion and high-nickel stability are engineered around (confidence 0.90). Lithium-metal and solid-state cells could give a larger gain at the cell level, but interface resistance, dendrites, pressure requirements, manufacturing and cost still limit their readiness for cars (0.86). Lithium–sulfur and lithium–air have very high theoretical energy but remain longer-horizon research (0.93).

Here is the full report:

# Research Report

## Question
what are the most promising approaches to improving battery energy density for electric vehicles?

## Executive Summary
The verified evidence supports a staged EV-battery development outlook. In the near term, silicon-rich anodes and high-nickel layered-oxide cathodes can raise energy density, but only with engineering that addresses silicon expansion and high-nickel stability, safety, and lifetime constraints. …
```

The report is Markdown, in the shape the method's template gives it: a "Research Report" title, then the question word for word, an executive summary, key findings naming approaches such as solid-state electrolytes, silicon anodes or lithium-sulfur cells, and the open questions they leave, closed by a "Generated by Pipelex" footer.

Saving the run writes its whole output as `runs/<run_id>/main_stuff.json` and reports the path:

```text
I saved the run. Its whole output is in runs/run_…/main_stuff.json (2,858 bytes). The output referenced no stored files, so that JSON file is the only thing saved.
```

## How it is built

The recipe is a request to your agent, so it carries no code: the plugin's [`/pipelex-run`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-run/SKILL.md) skill does the work through the Pipelex tools.

- **The inputs.** The agent takes the address as the method's `method_ref`, reads the question from your request, and checks it against the method's input template (`mthds_inputs_template`). Had you not given the question, it would look for the method's inputs in `./research_report/`, the directory named after the address, where `/pipelex-inputs` writes them.
- **The proof.** `mthds_validate` validates the method at its address before any credit is spent, and a dry run ends there. A published method that fails validation is reported with its address and its tag, and is not yours to repair: another tag, or its publisher, is the fix.
- **The run.** `mthds_run` starts it and returns its id at once, with its `method_provenance`. `mthds_run_status` follows it, waiting as long as the API asks between two readings, and a status marked `degraded` is read as the last one known, never as a stuck or failed run.
- **The results.** `mthds_run_results` reads the output of a run that has ended, and `mthds_download_artifacts` saves it, days after the run as well. Before saving into a git repository, the agent makes sure `runs/` is ignored, adding it to `.gitignore` when it is not, and says so.
- **The address is pinned** to a release tag, so the run executes the method as it was at that release. An address without a tag runs whatever its default branch holds at the moment, and the agent says so in one line.
- The same lifecycle, without an agent: the [HTTP recipe](../http/) makes the three calls with `curl`, and the [durable run](../../code/typescript/durable-run/) recipe makes them with the TypeScript SDK.
