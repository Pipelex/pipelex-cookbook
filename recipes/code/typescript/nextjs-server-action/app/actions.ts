"use server";

import { PipelineRequestError } from "@pipelex/sdk";
import { ZodError } from "zod";

import { parseDataRecord, serializeDataDescription, serializeRecordCount } from "../generated/gen_synthetic_data/binder";
import type { DataRecord } from "../generated/gen_synthetic_data/types";
import { MAX_DESCRIPTION_LENGTH, MAX_RECORDS } from "../lib/limits";
import { pipelexClient } from "../lib/pipelex";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/gen_synthetic_data@v0.20.0";

/** What the form shows in its fields: the sample values at first, then what the visitor last sent. */
export type FormValues = { description: string; count: string };

export type RecordsState = { values: FormValues } & (
  | { status: "idle" }
  | { status: "generated"; records: DataRecord[]; runId: string }
  | { status: "refused"; message: string }
);

/**
 * The form's server action: check the request, send it as the method's own input types, run the method by its address,
 * and hand the page the records, typed by the method's output type. Every answer carries the values the visitor sent,
 * since React resets a form once its action has run.
 */
export async function generateRecords(_previous: RecordsState, form: FormData): Promise<RecordsState> {
  const values = formValues(form);
  const refused = (message: string): RecordsState => ({ values, status: "refused", message });
  // The browser sends a textarea's line breaks as CRLF, two characters where its maxLength counted one, so the action
  // counts, and sends to the run, the text as the visitor typed it.
  const description = values.description.replaceAll("\r\n", "\n").trim();
  if (!description) {
    return refused("Describe the records you want.");
  }
  if (description.length > MAX_DESCRIPTION_LENGTH) {
    return refused(`The description is longer than ${MAX_DESCRIPTION_LENGTH} characters.`);
  }
  const count = Number(values.count);
  if (!Number.isInteger(count) || count < 1 || count > MAX_RECORDS) {
    return refused(`The number of records must be a whole number from 1 to ${MAX_RECORDS}.`);
  }
  try {
    const results = await pipelexClient().startAndWaitForResult({
      method_ref: METHOD_REF,
      inputs: {
        data_description: { concept: "synthetic_data_generation.DataDescription", content: serializeDataDescription({ text: description }) },
        nb_samples: { concept: "synthetic_data_generation.RecordCount", content: serializeRecordCount({ number: count }) },
      },
    });
    const items = listItems(results.main_stuff);
    if (items === undefined) {
      return refused(`The method answered with something other than a list of records, in run ${results.pipeline_run_id}.`);
    }
    return { values, status: "generated", records: items.map((item) => parseDataRecord(item)), runId: results.pipeline_run_id };
  } catch (error) {
    // A refused, failed or timed-out run, or an answer the generated types do not accept: the page says why.
    if (error instanceof PipelineRequestError || error instanceof ZodError) {
      return refused(error.message);
    }
    throw error;
  }
}

/** The items of a list output: the SDK documents the envelope {"items": [...]}, while the hosted API answers a bare list today. */
function listItems(mainStuff: unknown): unknown[] | undefined {
  if (Array.isArray(mainStuff)) {
    return mainStuff;
  }
  if (typeof mainStuff === "object" && mainStuff !== null && "items" in mainStuff && Array.isArray(mainStuff.items)) {
    return mainStuff.items;
  }
  return undefined;
}

/** Each field of the form as it sent it; a missing field, or a file in its place, reads as empty. */
function formValues(form: FormData): FormValues {
  const value = (field: keyof FormValues) => {
    const entry = form.get(field);
    return typeof entry === "string" ? entry : "";
  };
  return { description: value("description"), count: value("count") };
}
