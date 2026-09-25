# A Next.js form whose server action runs a method

Your site needs a form that writes something for its visitor: here, a blog article from a topic, an audience, a tone and a length. This recipe is a Next.js app with one page whose server action runs the cookbook's [blog article generator](../../../../methods/blog_article_generator/) by its address, and renders the article it returns.

It shows how a method becomes part of a web app:

- **The key stays on the server.** The server action is the only code that calls the hosted API, through one `PipelexApiClient` for the whole server process, which reads `PIPELEX_API_KEY` from the server's environment. The browser sends the form and gets the article back, and never sees the key.
- **The method's types on both sides.** The action validates the form against `BlogArticleRequestSchema`, generated from the method's input, before spending a run, and reads the answer through `parseBlogArticle`, generated from its output, so the page renders typed fields. The page's tone and length choices come from the same schema instead of being copied by hand.
- **Failures as messages.** A form the method would refuse, a run that fails, or an answer the types do not accept comes back to the page as a message saying why, instead of a server error.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each article is one run on the hosted API and spends credit.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run dev
```

Then open http://127.0.0.1:3000, and write an article with the form's sample values or your own.

## What you get

The article under the form: its title for search engines, the description they show under it, and its body in Markdown, with the id of the run that wrote it. On the sample values, the title reads like "Capybara Fun Facts for Kids" and the body runs to a few hundred words.

## Before you deploy it

The app has no authentication of its own, and every article it writes is a run on your key's credit. Run as above, `npm run dev` and `npm start` listen on `127.0.0.1` only, so nothing but your own machine reaches the form. Deployed, anyone who reaches the page spends your credit. A server action is also a public endpoint that anyone can post to directly, without the page, so the guard belongs in the action itself: check your site's own session at its top, and put a rate limit in front of it, before it faces a network. The action already refuses a field longer than a thousand characters.

## How it is built

- `app/actions.ts` is the server action. It calls the method by its address, `github.com/Pipelex/pipelex-cookbook/blog_article_generator@v0.18.0`, pinned to a release tag so the method never changes under the types, and waits for the run with `startAndWaitForResult`.
- `app/page.tsx` is the form, a client component that calls the action through React's `useActionState`. React resets a form once its action has run, so the action sends back what the visitor typed with every answer, and the form shows it again. `lib/pipelex.ts` holds the client, and only server code imports it.
- `generated/blog_article_generator/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- An article comes back while the visitor waits, which a server action can do. A method that runs for many minutes belongs in the [durable run](../durable-run/) pattern instead: start the run in the action, return its id, and let the page ask for the result.
