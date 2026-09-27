/**
 * Start a release post on the hosted API and print its run id, without waiting for it.
 *
 *     npm run start-run -- <release notes> <style guide>    # two text or Markdown files
 *     npm run start-run -- --sample                         # the method's own sample notes and guide
 *
 * The method turns a release's engineering notes into a post for the company blog, as the company's style guide says.
 * The run carries on server-side whatever this process does next: keep the id it prints, and read the post later,
 * from any machine holding the same key, with `npm run result -- <run id>`. PIPELEX_API_KEY must be set; each post
 * is one run and spends credit.
 */
import { readFile } from "node:fs/promises";

import { PipelexApiClient } from "@pipelex/sdk";
import { z } from "zod";

import { parseReleaseNotes, parseStyleGuide, serializeReleaseNotes, serializeStyleGuide } from "./generated/write_release_post/binder";
import type { ReleaseNotes, StyleGuide } from "./generated/write_release_post/types";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/write_release_post@v0.20.0";
const SAMPLE_INPUTS_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/methods/write_release_post/inputs.json";

/** The part of the method's sample inputs this script reads: each input's content, which the generated types then read. */
const SampleInputsSchema = z.object({
  release_notes: z.object({ content: z.unknown() }),
  style_guide: z.object({ content: z.unknown() }),
});

/** The method's sample release notes and style guide, from the inputs its cookbook page links to. */
async function sampleInputs(): Promise<{ notes: ReleaseNotes; guide: StyleGuide }> {
  const response = await fetch(SAMPLE_INPUTS_URL);
  if (!response.ok) {
    throw new Error(`the sample inputs answered HTTP ${response.status}`);
  }
  const sample = SampleInputsSchema.parse(await response.json());
  return { notes: parseReleaseNotes(sample.release_notes.content), guide: parseStyleGuide(sample.style_guide.content) };
}

/** The notes and the guide the command line names: two files, or `--sample`. */
async function readInputs(args: string[]): Promise<{ notes: ReleaseNotes; guide: StyleGuide }> {
  if (args.length === 1 && args[0] === "--sample") {
    return sampleInputs();
  }
  const [notesPath, guidePath] = args;
  if (args.length === 2 && notesPath && guidePath) {
    return { notes: { text: await readFile(notesPath, "utf8") }, guide: { text: await readFile(guidePath, "utf8") } };
  }
  console.error("usage: npm run start-run -- <release notes file> <style guide file>  |  npm run start-run -- --sample");
  process.exit(2);
}

const { notes, guide } = await readInputs(process.argv.slice(2));

const client = new PipelexApiClient();
const { pipeline_run_id: runId } = await client.start({
  method_ref: METHOD_REF,
  inputs: {
    release_notes: { concept: "release_post.ReleaseNotes", content: serializeReleaseNotes(notes) },
    style_guide: { concept: "release_post.StyleGuide", content: serializeStyleGuide(guide) },
  },
});
console.error(`started; read the post later with: npm run result -- ${runId}`);
console.log(runId);
