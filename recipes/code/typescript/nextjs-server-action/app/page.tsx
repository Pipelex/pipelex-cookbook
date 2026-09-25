"use client";

import { useActionState } from "react";

import { BlogArticleRequestSchema } from "../generated/blog_article_generator/types";
import { writeArticle, type ArticleState } from "./actions";

// The choices the method accepts, read from its generated input type rather than copied by hand.
const TONES = BlogArticleRequestSchema.shape.tone.options;
const LENGTHS = BlogArticleRequestSchema.shape.length.options;

const SAMPLE: ArticleState = {
  status: "idle",
  values: { topic: "Capybara", audience: "Kids", text: "Write a fun and engaging blog article", tone: "Casual", length: "Short" },
};

export default function Page() {
  const [state, submit, pending] = useActionState(writeArticle, SAMPLE);
  const { values } = state;
  return (
    <main>
      <h1>Write a blog article</h1>
      {/* React resets the form once its action has run, each field to its default: the values the action sent back. */}
      <form action={submit} style={{ display: "grid", gap: "0.75rem" }}>
        <label>
          Topic <input name="topic" required defaultValue={values.topic} />
        </label>
        <label>
          Audience <input name="audience" required defaultValue={values.audience} />
        </label>
        <label>
          Instructions <input name="text" required defaultValue={values.text} />
        </label>
        {/* A select reads its default only when it mounts, so each one is keyed on its default to mount again when it changes. */}
        <label>
          Tone{" "}
          <select key={values.tone} name="tone" defaultValue={values.tone}>
            {TONES.map((tone) => (
              <option key={tone}>{tone}</option>
            ))}
          </select>
        </label>
        <label>
          Length{" "}
          <select key={values.length} name="length" defaultValue={values.length}>
            {LENGTHS.map((length) => (
              <option key={length}>{length}</option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={pending}>
          {pending ? "Writing…" : "Write it"}
        </button>
      </form>
      {state.status === "refused" && <p role="alert">{state.message}</p>}
      {state.status === "written" && (
        <article>
          <h2>{state.article.seo_title}</h2>
          <p>
            <em>{state.article.meta_description}</em>
          </p>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{state.article.content}</pre>
          <small>run {state.runId}</small>
        </article>
      )}
    </main>
  );
}
