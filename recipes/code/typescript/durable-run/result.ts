/**
 * Read a research report by its run id, however long ago the run started.
 *
 *     npm run result -- <run id>           # prints the report if the run is done, or says it is still going
 *     npm run result -- <run id> --wait    # waits for the run to end, then prints the report
 *
 * The report goes to stdout as Markdown, so `npm run --silent result -- <run id> > report.md` saves it.
 * PIPELEX_API_KEY must be set: a run is read with the key of the account that started it. Reading spends no credit.
 */
import { PipelexApiClient, RunFailedError, RunTimeoutError } from "@pipelex/sdk";

import { parseFormattedReport } from "./generated/research_report/binder";

const STILL_RUNNING = 3;
const POLL_INTERVAL_MS = 10_000;

const [runId, ...flags] = process.argv.slice(2);
if (!runId) {
  console.error("usage: npm run result -- <run id> [--wait]");
  process.exit(2);
}

/** The report's Markdown, from a completed run's main output, typed by the method's `FormattedReport`. */
function reportOf(mainStuff: unknown): string {
  return parseFormattedReport(mainStuff).text;
}

const client = new PipelexApiClient();
if (flags.includes("--wait")) {
  try {
    const results = await client.waitForResult(runId, {
      intervalMs: POLL_INTERVAL_MS,
      onPoll: ({ elapsedMs }) => console.error(`… still going after ${Math.round(elapsedMs / 1000)}s`),
    });
    console.log(reportOf(results.main_stuff));
  } catch (error) {
    if (error instanceof RunTimeoutError) {
      // The wait ended, not the run: it carries on server-side, and the same command picks it up again.
      console.error(`run ${error.runId} is still going after the wait; ask again later`);
      process.exit(STILL_RUNNING);
    }
    if (error instanceof RunFailedError) {
      console.error(`run ${error.runId} ended ${error.status}: ${error.message}`);
      process.exit(1);
    }
    throw error;
  }
} else {
  const state = await client.getRunResult(runId);
  switch (state.state) {
    case "running":
      console.error(`run ${runId} is still going; ask again later, or pass --wait`);
      process.exit(STILL_RUNNING);
    case "failed":
      console.error(`run ${runId} ended ${state.status}: ${state.message}`);
      process.exit(1);
    case "completed":
      console.log(reportOf(state.result.main_stuff));
  }
}
