/**
 * Read a research report by its run id, however long ago the run started.
 *
 *     npm run result -- <run id>           # prints the report if the run is done, or says it is still going
 *     npm run result -- <run id> --wait    # waits up to twenty minutes for the run to end, then prints the report
 *
 * The report goes to stdout as Markdown, so `npm run --silent result -- <run id> > report.md` saves it.
 * PIPELEX_API_KEY must be set: a run is read with the key of the account that started it. Reading spends no credit.
 *
 * The exit status tells a scheduler what to do next: 0 with the report, 3 while the run is still going, 4 when the run
 * could not be read at all (the API unreachable, the lookup refused), both worth asking again, and 1 when the run failed.
 */
import { PipelexApiClient, RunFailedError, RunTimeoutError } from "@pipelex/sdk";

import { parseFormattedReport } from "./generated/research_report/binder";

const RUN_FAILED = 1;
const STILL_RUNNING = 3;
const LOOKUP_FAILED = 4;
const POLL_INTERVAL_MS = 10_000;
const WAIT_TIMEOUT_MS = 20 * 60_000;

const [runId, ...flags] = process.argv.slice(2);
if (!runId) {
  console.error("usage: npm run result -- <run id> [--wait]");
  process.exit(2);
}

/** The report's Markdown, from a completed run's main output, typed by the method's `FormattedReport`. */
function reportOf(mainStuff: unknown): string {
  return parseFormattedReport(mainStuff).text;
}

/** Print the report, or say why there is none, and answer the exit status. An error reading the run is thrown. */
async function readRun(client: PipelexApiClient, runId: string, wait: boolean): Promise<number> {
  if (wait) {
    try {
      const results = await client.waitForResult(runId, {
        intervalMs: POLL_INTERVAL_MS,
        timeoutMs: WAIT_TIMEOUT_MS,
        onPoll: ({ elapsedMs }) => console.error(`… still going after ${Math.round(elapsedMs / 1000)}s`),
      });
      console.log(reportOf(results.main_stuff));
      return 0;
    } catch (error) {
      if (error instanceof RunTimeoutError) {
        // The wait ended, not the run: it carries on server-side, and the same command picks it up again.
        console.error(`run ${error.runId} is still going after the wait; ask again later`);
        return STILL_RUNNING;
      }
      if (error instanceof RunFailedError) {
        console.error(`run ${error.runId} ended ${error.status}: ${error.message}`);
        return RUN_FAILED;
      }
      throw error;
    }
  }
  const state = await client.getRunResult(runId);
  switch (state.state) {
    case "running":
      console.error(`run ${runId} is still going; ask again later, or pass --wait`);
      return STILL_RUNNING;
    case "failed":
      console.error(`run ${runId} ended ${state.status}: ${state.message}`);
      return RUN_FAILED;
    case "completed":
      console.log(reportOf(state.result.main_stuff));
      return 0;
  }
}

try {
  process.exitCode = await readRun(new PipelexApiClient(), runId, flags.includes("--wait"));
} catch (error) {
  // The run could not be read, which says nothing about the run itself: it may be going, or done, and asking again may work.
  console.error(`could not read run ${runId}: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = LOOKUP_FAILED;
}
