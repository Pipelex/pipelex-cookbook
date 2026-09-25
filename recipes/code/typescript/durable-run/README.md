# A run started now and read hours later

Some methods take minutes: a report that drafts, checks and formats its answer is one. Nothing needs to wait for it. This recipe starts the cookbook's [research report](../../../../methods/research_report/) method on the hosted API, prints the run's id and exits; a second command, run whenever you like, reads the report by that id.

It shows the run lifecycle behind every method call:

- **A run outlives its caller.** `start` returns as soon as the hosted API has accepted the run, with its id. The run carries on server-side whether the process that started it waits, exits or crashes.
- **An id is all it takes to come back.** `getRunResult` answers at once, with the result or with the news that the run is still going, and `waitForResult` polls until it ends. Either works from another process, another machine or the next day, with a key of the same account.
- **Waiting is not failing.** When a wait ends first, the run is still going, and asking again later picks it up; only a run that ended in failure is one.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each report is one run on the hosted API and spends credit; reading a run spends none.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run --silent start-run -- "What are the most promising approaches to improving battery energy density for electric vehicles?"
```

It prints the run's id, such as `run_8bf12c67-…`. Later, read the report:

```bash
npm run --silent result -- run_8bf12c67-…            # the report if the run is done, or a line saying it is still going
npm run --silent result -- run_8bf12c67-… --wait     # waits up to twenty minutes for the run to end, then prints the report
npm run --silent result -- run_8bf12c67-… > report.md
```

## What you get

The report in Markdown on stdout: the question, an executive summary, the key findings from its three angles, and the questions it leaves open. A run that is still going exits with status 3, and one that failed exits with status 1 and says why. When the API is out of reach or answers with a server error, the script exits with status 4, which says nothing about the run itself. When the run cannot be read as asked, because its id is unknown, the key is refused or the report does not match the generated types, it exits with status 5, since asking again gives the same answer. A scheduler asks again on 3 and 4, and stops on 1 and 5.

## How it is built

- `start.ts` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0`, pinned to a release tag so the method never changes under the types, with `start`.
- `result.ts` reads the run with `getRunResult`, or with `waitForResult` under `--wait`, and reads the report through `parseFormattedReport`, generated from the method's output.
- `generated/research_report/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- A web app follows the same shape: its server starts the run and returns the id, and its page asks for the result until it is there.
