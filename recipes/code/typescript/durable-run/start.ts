/**
 * Start a research report on the hosted API and print its run id, without waiting for it.
 *
 *     npm run start-run -- "What are the most promising approaches to improving battery energy density?"
 *
 * The run carries on server-side whatever this process does next: keep the id it prints, and read the report
 * later, from any machine holding the same key, with `npm run result -- <run id>`. PIPELEX_API_KEY must be set;
 * each report is one run and spends credit.
 */
import { PipelexApiClient } from "@pipelex/sdk";

import { serializeResearchQuestion } from "./generated/research_report/binder";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/research_report@v0.18.0";

const question = process.argv.slice(2).join(" ").trim();
if (!question) {
  console.error('usage: npm run start-run -- "<the question the report answers>"');
  process.exit(2);
}

const client = new PipelexApiClient();
const { pipeline_run_id: runId } = await client.start({
  method_ref: METHOD_REF,
  inputs: { question: { concept: "research_report.ResearchQuestion", content: serializeResearchQuestion({ text: question }) } },
});
console.error(`started; read the report later with: npm run result -- ${runId}`);
console.log(runId);
