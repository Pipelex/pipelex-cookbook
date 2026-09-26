# A method over HTTP: start, poll, results

Any tool that makes HTTP calls can run a method, with no SDK: one call starts the run and answers at once with its id, a second reads how the run is going, and a third reads its results. This recipe makes those three calls with `curl` in a small shell script, to read a French energy performance diagnostic with the cookbook's [DPE extraction](../../../methods/extract_dpe/) method. The same three calls are how n8n, Zapier or any tool that makes HTTP calls reaches a method.

It shows the run lifecycle as the hosted API serves it:

- **A run outlives the call that started it.** The start answers `202` with the run's id before the method has done anything, and the run carries on server-side whatever the caller does next. The id is all it takes to read the run later, from anywhere, with a key of the same account.
- **Polling follows the server's pace.** The status route names the run's state, and its `Retry-After` header says how long to wait before asking again. A status marked `degraded` is the last one the API knew rather than a fresh reading, so the script keeps asking.
- **Every outcome has its own exit status.** An output, a failed run, a run still going when the wait ends, an API out of reach and a refused request each end the script differently, so a scheduler knows whether to ask again.

## What it needs

- [curl](https://curl.se/), and [jq](https://jqlang.org/) to build the request and read the answers.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each start is one run on the hosted API and spends credit; following a run spends none.

## Run it

```bash
export PIPELEX_API_KEY=…
sh run.sh https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/extract_dpe/dpe_single_page.pdf > dpe.json
```

The document is the cookbook's sample DPE, linked at the release tag `v0.18.0`. Any DPE works, as long as its URL is one the hosted API can fetch, such as a public link, a presigned URL or a `pipelex-storage://` uri from an [upload grant](../../code/typescript/upload-grant/). The script prints its progress to the terminal and the method's output to `dpe.json`.

A run can also be started now and read later, by its id alone:

```bash
WAIT_SECONDS=0 sh run.sh https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/extract_dpe/dpe_single_page.pdf   # prints the run's id and exits with status 3
sh run.sh --run run_… > dpe.json   # whenever you like: waits for the run to end, then prints its output
```

`WAIT_SECONDS` bounds the wait, twenty minutes by default.

## What you get

The terminal shows the run's id as soon as the start answers, with the commit the tag resolved to, then the run's state at each poll:

```text
started run_…
method github.com/Pipelex/pipelex-cookbook/extract_dpe at v0.18.0, commit 42dcaa9a5eafe62752ea8a5f7f57e5d83a2cca87
… RUNNING after 1s
… RUNNING after 6s
… RUNNING after 12s
… RUNNING after 18s
… RUNNING after 23s
run run_… completed
```

`dpe.json` holds the method's output, a `Dpe`:

```json
{
  "address": "51 rue du Roi de Sicile, 75004 PARIS - 4EME",
  "date_of_issue": "2022-03-29",
  "date_of_expiration": "2032-03-28",
  "energy_efficiency_class": "G",
  "per_year_per_m2_consumption": 560.0,
  "co2_emission_class": "C",
  "per_year_per_m2_co2_emissions": 18.0,
  "yearly_energy_costs_min": 1260.0,
  "yearly_energy_costs_max": 1750.0
}
```

These are the figures printed on the sample diagnostic: the address at 51 rue du Roi de Sicile, 75004 Paris; issued on 2022-03-29 and valid until 2032-03-28; energy class G at 560 kWh per m² per year; CO₂ class C at 18 kg per m² per year; and yearly energy costs between 1260 and 1750 euros.

The exit status says what happened, in the pattern of the [durable run](../../code/typescript/durable-run/) recipe:

| Status | What happened | What a scheduler does |
|---|---|---|
| 0 | The run completed, and its output is on stdout | Nothing more |
| 1 | The run ended without a result: `FAILED`, `CANCELLED`, `TERMINATED` or `TIMED_OUT`. The script prints the error the run's record carries, when it has one | Stops |
| 2 | The script was called wrongly, or `curl`, `jq` or the key is missing | Stops |
| 3 | The run was still going when the wait ended | Asks again with `--run` |
| 4 | The API was out of reach, answered with a server error, or answered in a way the script cannot read | Asks again with `--run`; after a start, no run id came back, so check your runs at [app.pipelex.com](https://app.pipelex.com) before starting another |
| 5 | The API refused the request: a key it does not accept, an input the method does not take, or a run id it does not know | Stops |

## How it is built

### The three calls

**Start.** `POST /v1/start` with the method's address as `method_ref` and its inputs, the key in the `Authorization` header:

```bash
curl -s https://api.pipelex.com/v1/start \
  -H "Authorization: Bearer $PIPELEX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"method_ref": "github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.18.0", "inputs": {"document": {"url": "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/extract_dpe/dpe_single_page.pdf"}}}'
# 202 → {"pipeline_run_id": "run_…", "method_provenance": {"address": "…", "tag": "v0.18.0", "commit_sha": "…"}}
```

The answer comes before the method runs, with the run's id and, for a run by address, its provenance: the address, the tag, and the commit the tag resolved to. A request the API refuses gets a `4xx` status whose body says why.

**Status.** `GET /v1/runs/{pipeline_run_id}/status` answers the run's record:

```bash
curl -s https://api.pipelex.com/v1/runs/$RUN_ID/status -H "Authorization: Bearer $PIPELEX_API_KEY"
```

Its `status` is one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TERMINATED` and `TIMED_OUT`. The last five are terminal, and only `COMPLETED` has results. When `degraded` is `true`, the status is the last one the API recorded rather than a fresh reading, and the `Retry-After` header says how many seconds to wait before asking again.

**Results.** `GET /v1/runs/{pipeline_run_id}/results` answers `202` while the run is going, `200` with the results once it has completed, and `409` if it ended without a result:

```bash
curl -s https://api.pipelex.com/v1/runs/$RUN_ID/results -H "Authorization: Bearer $PIPELEX_API_KEY"
```

The method's output is the results' `main_stuff`. Beside it come the run's working memory, the graph it executed and the usage of each inference call. A client that needs no progress on the way can poll this route alone, as the snippet on each method page does, until it answers something other than `202`.

### In n8n, Zapier or any tool that makes HTTP calls

Each call is one HTTP request step: the start as a `POST` with the JSON body above, then the status in a loop with a wait between two readings until it is terminal, then the results. The key goes in an `Authorization: Bearer` header, kept in the tool's store of credentials rather than written into the workflow. In n8n, that is n8n's own HTTP Request node: the [Pipelex node](https://github.com/Pipelex/n8n-nodes-pipelex) starts a run and polls its results through the same routes, but for a saved method named by its Method ID or a method pasted into it, and it takes no address today.

### The script

- `run.sh` holds the method's address in `METHOD_REF`, pinned to a release tag, so what it runs never changes under it.
- It builds the request body with `jq`, so a document URL holding a quote cannot break the JSON, and reads each answer with `jq`.
- It hands the key to `curl` on its standard input, as a line of configuration, rather than as an argument, so the key does not show in the process list, and it never prints it.
- It waits five seconds between two readings of the status, or longer when `Retry-After` asks for it, and reads a status it does not know as a run still going.
- With the SDKs, these calls are made for you: the [durable run](../../code/typescript/durable-run/) recipe starts a run and reads it later by its id in TypeScript, and a [coding agent](../coding-agent/) does the same from a sentence.
