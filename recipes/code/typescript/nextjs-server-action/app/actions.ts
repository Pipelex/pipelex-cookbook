"use server";

import { PipelineRequestError } from "mthds/errors";
import { ZodError, z } from "zod";

import { parseBlogArticle } from "../generated/blog_article_generator/binder";
import { BlogArticleRequestSchema, type BlogArticle } from "../generated/blog_article_generator/types";
import { pipelexClient } from "../lib/pipelex";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/blog_article_generator@v0.18.0";

export type ArticleState =
  | { status: "idle" }
  | { status: "written"; article: BlogArticle; runId: string }
  | { status: "refused"; message: string };

/**
 * The form's server action: validate the request against the method's own input type, run the method by its address,
 * and hand the page the article, typed by the method's output type.
 */
export async function writeArticle(_previous: ArticleState, form: FormData): Promise<ArticleState> {
  const request = BlogArticleRequestSchema.safeParse(Object.fromEntries(form));
  if (!request.success) {
    return { status: "refused", message: z.prettifyError(request.error) };
  }
  try {
    const results = await pipelexClient().startAndWaitForResult({
      method_ref: METHOD_REF,
      inputs: { user_prompt: { concept: "blog_article_generator.BlogArticleRequest", content: request.data } },
    });
    return { status: "written", article: parseBlogArticle(results.main_stuff), runId: results.pipeline_run_id };
  } catch (error) {
    // A refused, failed or timed-out run, or an answer the generated types do not accept: the page says why.
    if (error instanceof PipelineRequestError || error instanceof ZodError) {
      return { status: "refused", message: error.message };
    }
    throw error;
  }
}
