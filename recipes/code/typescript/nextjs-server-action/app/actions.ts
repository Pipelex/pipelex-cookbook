"use server";

import { PipelineRequestError } from "@pipelex/sdk";
import { ZodError, z } from "zod";

import { parseBlogArticle } from "../generated/blog_article_generator/binder";
import { BlogArticleRequestSchema, type BlogArticle, type BlogArticleRequest } from "../generated/blog_article_generator/types";
import { pipelexClient } from "../lib/pipelex";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/blog_article_generator@v0.18.0";
// The generated input type bounds no text, and every request spends a run on your key: a field past this length is refused.
const MAX_FIELD_LENGTH = 1_000;

/** What the form shows in its fields: the sample values at first, then what the visitor last sent. */
export type FormValues = Record<keyof BlogArticleRequest, string>;

export type ArticleState = { values: FormValues } & (
  | { status: "idle" }
  | { status: "written"; article: BlogArticle; runId: string }
  | { status: "refused"; message: string }
);

/**
 * The form's server action: validate the request against the method's own input type, run the method by its address,
 * and hand the page the article, typed by the method's output type. Every answer carries the values the visitor sent,
 * since React resets a form once its action has run.
 */
export async function writeArticle(_previous: ArticleState, form: FormData): Promise<ArticleState> {
  const values = formValues(form);
  const tooLong = Object.entries(values).find(([, value]) => value.length > MAX_FIELD_LENGTH);
  if (tooLong) {
    return { values, status: "refused", message: `The ${tooLong[0]} field is longer than ${MAX_FIELD_LENGTH} characters.` };
  }
  const request = BlogArticleRequestSchema.safeParse(values);
  if (!request.success) {
    return { values, status: "refused", message: z.prettifyError(request.error) };
  }
  try {
    const results = await pipelexClient().startAndWaitForResult({
      method_ref: METHOD_REF,
      inputs: { user_prompt: { concept: "blog_article_generator.BlogArticleRequest", content: request.data } },
    });
    return { values, status: "written", article: parseBlogArticle(results.main_stuff), runId: results.pipeline_run_id };
  } catch (error) {
    // A refused, failed or timed-out run, or an answer the generated types do not accept: the page says why.
    if (error instanceof PipelineRequestError || error instanceof ZodError) {
      return { values, status: "refused", message: error.message };
    }
    throw error;
  }
}

/** Each field the method's input type names, as the form sent it; a missing field, or a file in its place, reads as empty. */
function formValues(form: FormData): FormValues {
  const value = (field: keyof FormValues) => {
    const entry = form.get(field);
    return typeof entry === "string" ? entry : "";
  };
  return { text: value("text"), topic: value("topic"), audience: value("audience"), tone: value("tone"), length: value("length") };
}
