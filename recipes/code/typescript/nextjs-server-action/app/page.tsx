"use client";

import { useActionState } from "react";

import { BlogArticleRequestSchema } from "../generated/blog_article_generator/types";
import { writeArticle, type ArticleState } from "./actions";

// The choices the method accepts, read from its generated input type rather than copied by hand.
const TONES = BlogArticleRequestSchema.shape.tone.options;
const LENGTHS = BlogArticleRequestSchema.shape.length.options;

const IDLE: ArticleState = { status: "idle" };

export default function Page() {
  const [state, submit, pending] = useActionState(writeArticle, IDLE);
  return (
    <main>
      <h1>Write a blog article</h1>
      <form action={submit} style={{ display: "grid", gap: "0.75rem" }}>
        <label>
          Topic <input name="topic" required defaultValue="Capybara" />
        </label>
        <label>
          Audience <input name="audience" required defaultValue="Kids" />
        </label>
        <label>
          Instructions <input name="text" required defaultValue="Write a fun and engaging blog article" />
        </label>
        <label>
          Tone{" "}
          <select name="tone" defaultValue="Casual">
            {TONES.map((tone) => (
              <option key={tone}>{tone}</option>
            ))}
          </select>
        </label>
        <label>
          Length{" "}
          <select name="length" defaultValue="Short">
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
