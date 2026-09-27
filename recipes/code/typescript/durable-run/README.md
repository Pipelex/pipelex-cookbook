# A run started now and read hours later

Some methods take minutes, and nothing needs to wait for them. This recipe starts the cookbook's [release post](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/write_release_post) method on the hosted API, which turns a release's engineering notes into a post for the company blog as the company's style guide says, prints the run's id and exits; a second command, run whenever you like, reads the post by that id.

It shows the run lifecycle behind every method call:

- **A run outlives its caller.** `start` returns as soon as the hosted API has accepted the run, with its id. The run carries on server-side whether the process that started it waits, exits or crashes.
- **An id is all it takes to come back.** `getRunResult` answers at once, with the result or with the news that the run is still going, and `waitForResult` polls until it ends. Either works from another process, another machine or the next day, with a key of the same account.
- **Waiting is not failing.** When a wait ends first, the run is still going, and asking again later picks it up; only a run that ended in failure is one.

## What it needs

- [Node.js](https://nodejs.org/) 22.12 or later.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each post is one run on the hosted API and spends credit; reading a run spends none.

## Run it

```bash
npm install
export PIPELEX_API_KEY=…
npm run --silent start-run -- --sample
```

`--sample` takes the method's own sample: the notes of a release of the Pipelex plugin, and a style guide written for the example. For your own release, name two text or Markdown files instead, the notes first: `npm run --silent start-run -- release-notes.md style-guide.md`.

It prints the run's id, such as `run_8bf12c67-…`. Later, read the post:

```bash
npm run --silent result -- run_8bf12c67-…            # the post if the run is done, or a line saying it is still going
npm run --silent result -- run_8bf12c67-… --wait     # waits up to twenty minutes for the run to end, then prints the post
npm run --silent result -- run_8bf12c67-… > post.md
```

## What you get

The post in Markdown on stdout, the fields the blog's CMS takes as front matter above its body, and on stderr, one line for each part of the release notes the post leaves out, with the style guide's rule that leaves it out, for whoever publishes it to check the cut. On the sample, read at once, the run was still going; read with `--wait`, it came within a minute, and the post began:

```markdown
---
title: "Manage saved methods with the Pipelex plugin"
slug: "manage-saved-methods-pipelex-plugin"
meta_description: "Manage saved methods by catalog ID, explain their stored source, and track linked runs in method history from your coding agent."
excerpt: "Manage saved methods from your coding agent, work by catalog ID, explain stored source, and see linked runs in method history."
category: "Product updates"
tags: ["Pipelex plugin","Methods","Catalog","SDK"]
---

In Pipelex plugin 0.7.0, you can manage your organization’s saved methods from your coding agent, work on them by catalog ID, and explain their stored source. …

## Manage saved methods from your coding agent
…
```

and stderr listed what it left out, such as:

```text
left out: Searching `pipelex-method.json` files to resolve a catalog ID (Rule 3: Leave out configuration and link-file mechanics.)
```

A run that is still going exits with status 3, and one that failed exits with status 1 and says why. When the API is out of reach or answers with a server error, the script exits with status 4, which says nothing about the run itself. When the run cannot be read as asked, because its id is unknown, the key is refused or the post does not match the generated types, it exits with status 5, since asking again gives the same answer. A scheduler asks again on 3 and 4, and stops on 1 and 5.

## How it is built

- `start.ts` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/write_release_post@v0.20.0`, pinned to a release tag so the method never changes under the types, with `start`. It gives the notes and the guide as the method's `ReleaseNotes` and `StyleGuide`, through their generated `serialize…` functions, and `--sample` reads them from the method's `inputs.json` at that release.
- `result.ts` reads the run with `getRunResult`, or with `waitForResult` under `--wait`, and reads the post through `parseReleasePost`, generated from the method's output.
- `generated/write_release_post/` holds the method's types: `types.ts` and `binder.ts`, generated from the method at that tag, and `codegen.lock`, which vouches for them. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does. `npm run codegen:check` checks them against their lock offline, with `scripts/codegen-check.mjs`, copied as it is from the `pipelex-integrate` skill.
- A web app follows the same shape: its server starts the run and returns the id, and its page asks for the result until it is there.
