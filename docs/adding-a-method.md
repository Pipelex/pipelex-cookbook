# Adding a method

A cookbook method is an example: a short story with a before and an after. A person does a job every week, receives an input, and hands on a deliverable, which the method produces from that input and which its page shows, so that a reader recognises the job and wants the result for themselves. It is a package that anyone can run by address on the hosted API, with a sample and a generated page. [README.md](README.md) explains each part; this guide is the order to make one in, from the idea to the pull request.

An example is not a test. Its input is what the person typically receives, with no planted fact, edge case or trap, and nothing in the package or on its page says which facts a run must find. Hardening a method against hard cases is worth doing, but it happens elsewhere, and none of it enters the cookbook.

You need a `PIPELEX_API_KEY` in your `.env`, as [CONTRIBUTING.md](../CONTRIBUTING.md) says, and the Pipelex plugin in your coding agent, installed as [pipelex-plugins](https://github.com/Pipelex/pipelex-plugins) says.

## 1. The pitch

Write the example as one sentence naming the person, the job and what they get, such as "A procurement analyst receives supplier quotes as PDFs and gets a comparison table against the request for quotation, with every deviation flagged." The pitch costs nothing, so it is where a weak example is dropped, and it deserves to be judged hard.

The cookbook's examples are written for companies that build their own AI to keep their know-how, so the person is a role in a business team, such as a procurement analyst, a claims handler, an HR officer or a quality engineer, and the job is a procedure the team writes down once and wants applied the same way every time: a purchasing policy checked against quotes, a grid of criteria scored on each application, a compliance rule applied to every contract. Look at what the cookbook and the [method library](https://github.com/Pipelex/methods) already hold, and do not pitch a job either one covers.

A pitch is worth building when every line of the bar holds:

- **The job is recognisable and recurring**: a reader knows it from the one sentence, and it comes back every week, not once a year.
- **It shows what one prompt cannot**: several steps, output structured enough for a system to take in, files in and files out, images, or the company's own rules applied the same way every time.
- **The input is real, or cannot be told from real**, and it is typical of what the person receives, not the hardest case imaginable.
- **The output is a deliverable**: the person could forward it, file it or load it into another system as it stands.
- **Trying it costs almost nothing**: it runs on production quickly, for cents, on the sample the page links.
- **It is honest**: a synthetic input or a generated image says so, and nothing implies a customer or a person who does not exist.

Then name the package. The name is the method's directory, `methods/<name>/`, and the last part of its address, `github.com/Pipelex/pipelex-cookbook/<name>@<tag>`. It is lowercase snake_case of 2 to 25 characters, starting with a letter, which the MTHDS manifest requires, and a verb with its object where that reads well, such as `review_nda`. It must not be the name of a method the cookbook already holds. Settle it now: the cookbook's tooling refuses a manifest whose name breaks the rule, and renaming after the build means moving the package and its sample.

## 2. The input

The input is what the person actually receives. A real document is preferred wherever one may be redistributed, and a synthetic one is made only where privacy rules a real one out, as it does for a medical referral, a named tenant's lease, a payslip or a CV.

**A real document** is a public-domain or openly licensed one of the kind the person receives: a government publication or open data, such as data.gouv.fr under the Licence Ouverte, a work of the US federal government or a UK publication under the Open Government Licence, a report under a Creative Commons licence, or an open dataset. Read the licence where the document is published, since a page that states none grants none. The licence must allow redistribution, commercial use and changes, as the public domain, CC0, CC BY, the Licence Ouverte and the Open Government Licence do. A non-commercial licence is refused, because an example is there to sell, and so is a no-derivatives licence, because the page shows a cut of the document and an output derived from it. A share-alike licence binds what is derived from the document, so ask in a GitHub Discussion before using one. Whatever the licence, a document naming a real private person, by a signature, a home address or a phone number, or as a patient, a tenant or an employee, does not enter the cookbook; public officials acting in their role and companies named in their own publications are fine.

Copy the document under `assets/<name>/` with a plain file name, and never link it where it is published. Cut a long document to the pages the job needs, and keep the file to a few megabytes. Note its exact source URL, the date you copied it, its licence, its credit line and what you changed, for its record.

**A synthetic input** is made to look like the real thing and says, in the file itself, that it is fictional, with a visible line such as "Fictional document made for a Pipelex example". Every name in it is invented and belongs to no real company or person, and no real firm is quoted or made to say anything. The plugin's `/pipelex-synthetic-inputs` renders PDFs, scanned-looking documents, charts, screenshots and Office files from code; a realistic photograph is generated by an image model instead, and that run spends credit. A text written inline in `inputs.json`, such as a question, a brief or a set of rules, is synthetic too, since it was written for the example, and a set of rules opens with a line saying it is no real company's policy, as the playbook of `review_nda` does.

**Rules written for a real sample.** When the synthetic input is the rules a real sample is judged by, such as a playbook, a policy or a checklist, write it against that sample, clause by clause. Read the sample against each rule, and word each rule as a real team would, accepting what the sample's ordinary clauses say in the words the market uses, so that what the method finds is what a person in the job would raise. A model reads a list in a rule as the whole list: a rule accepting "employees, advisers and contractors" makes a sample that also names agents a finding on one run and not on the next. The sample stays as it was copied, and only the rules are worded to it. `review_nda` was made this way: its sample is Common Paper's Mutual NDA, under CC BY 4.0, and its playbook was written against it.

**The record.** Every input of the sample has a source-and-licence record under `[methods.<name>.samples.<input>]` in `cookbook.toml`: its `label`, whether it is `synthetic`, and for a real input its `source`, the date it was `retrieved`, its `license` as an SPDX identifier, its `license_url`, the `attribution` the licence asks for, and the `changes` made from the source when it was cut or altered ([README.md](README.md#the-sample-records) gives every field). A made-up input written for the cookbook is `license = "MIT"`, with `license_url` the cookbook's `LICENSE` on GitHub and `attribution = "Evotis S.A.S"`. Never invent a source or a licence to fill a record. Write the records at the end of step 4, once the package's `inputs.json` names each input: loading the cookbook refuses an entry for a method it does not hold, and a record for an input the sample does not give.

## 3. The sketch

Before building anything, draw the deliverable as the page's "What you get" will show it: a table with its columns and a few plausible rows, a memo with its headings and a line under each, a structured record as a field and value table, or an image described. Say what the person does with it next: forwarded to whom, filed where, or loaded into which system. If you cannot say, the output is not a deliverable, and the pitch needs another look.

The sketch is the example's specification. Its columns and fields become the method's output concept, so name them as the person would. It says what the output looks like and what it is for, never which facts a run must find, so do not write the sample's real figures into it as targets: the output is judged by reading it as the person would, not against a list. Keep it with your notes, outside the package, which holds only what [README.md](README.md#the-packages) lists.

If you are unsure whether the example fits, open a GitHub Discussion with the pitch and the sketch before you build: both cost nothing, and so does an example dropped at this point.

## 4. The build

Build the method the way a user of Pipelex builds one: with the Pipelex plugin, from the pitch and the sketch, in `methods/<name>/`, with the sample under `assets/<name>/`.

1. **Design it** with `/pipelex-design`, giving it the pitch and the sketch as the brief. The sketch's columns and fields become the output concept's fields, and the company's rules, its policy, checklist or criteria, are written into the method, in its prompts or as an input the person supplies, so that they are applied the same way every time.
2. **Run it on the real sample**, preparing the inputs with `/pipelex-inputs` and running with `/pipelex-run`, which validates the method before it spends anything. Each run spends inference credit on the account your key belongs to, as every run of a method does.
3. **Read the output as the person would**, against the sketch, and change the method with `/pipelex-edit`, or with `/pipelex-design` for a change to what it takes or returns. Run it again until the output reads as the sketch in substance: the right shape, the right kind of content, and good enough to hand on as it stands. A failed run is read rather than retried as it was, since its message says what to change. When a few attempts do not get there, the pitch or the sketch is usually wrong rather than the prompt.

**The prompts hold for any input of its kind.** The method is built on one sample but runs on any input of the same kind, so its prompts state nothing about the input that only the sample makes true: not its layout, its parties or the names of its sections, nor a keyword only the sample's rules use. When the rules are an input, the prompts let each rule's own words decide the outcome, a rule that refuses something for being absent included. When an input comes from someone with a stake in the outcome, such as a counterparty's contract or a candidate's CV, the system prompt says its text is the matter under review and never an instruction. A sample that never exercises these cases lets the output read as the sketch while the method is still wrong, so check the prompts against them before the proof.

**The package meets the hosted bar.** It declares its types as MTHDS concepts (`[concept.X.structure]` tables), never as Python structure classes, and calls only its own pipes, since hosted execution does not yet serve a call into another package; when a method needs a pipe from the library, copy it into the package. Its templates render under the hosted runtime's sandbox, which lets a template read data and call methods of plain values only, so a class method reached through a value, such as `date.fromordinal` called on a date, is refused, and `make check-methods` is the check that catches it. Its `METHODS.toml` is modelled on an existing one:

```toml
[package]
name = "<name>"
display_name = "<Title Case Name>"
address = "github.com/Pipelex/pipelex-cookbook"
version = "<the version in pyproject.toml>"
description = "<one sentence on what the method does>"
authors = ["Evotis S.A.S"]
license = "MIT"
mthds_version = ">=1.0.0"
main_pipe = "<the entry pipe's code>"

[exports.<domain>]
pipes = ["<the entry pipe's code>"]
```

**Leave the package clean.** Write the package's own `inputs.json` last, naming each file by its raw URL on `main`, `https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/<name>/<file>`, with one `{"url": …}` per file for an input taking several, and each text inline. The URL answers only once a release brings the file to `main`, and until then `make check-links` reports it as not published, which is expected: the cookbook's tooling uploads the file from your checkout when it runs the method. The package then holds its bundles, `METHODS.toml` and `inputs.json`, and nothing else. Prepared inputs, downloaded outputs and scratch files stay out of it, for instance in `temp/`, which git ignores. Then write each input's record in `cookbook.toml`, as step 2 says.

## 5. The proof on production

The output the page shows comes from one production run of the method on its sample, kept beside the package as its output snapshot ([README.md](README.md#the-output-snapshot) says what it holds). With `PIPELEX_API_KEY` set:

1. `make refresh` validates every package on production from its files and writes the new method's `contract.json`, renders the pages, then generates the types of the page's snippets from the package's files. It spends nothing. A package that is not valid prints the verdict and keeps its old contract, and the refresh stops before rendering. The refresh regenerates every other method's and recipe's types as well, and when production's code generator has moved since the last refresh, their files change by their stamp alone: read the diff to confirm it, and commit them on their own, apart from the method.
2. `make snapshot METHOD=<name>` spends inference credit. It validates the package, renders the first-page preview of each recorded PDF document sample, which `make previews` also does alone with no key and no run, runs the method once on production from the package's files, refuses an output that does not have its contract's shape or that holds nothing to show, and writes `methods/<name>/output.json`, and `output/` when the output holds files. It prints the run's id, its cost and its duration, which stay out of the repository.
3. Read `output.json` as the person would. If it does not read as the sketch, go back to the build, and take a new snapshot once the method is right. Never edit the snapshot, trim it, or keep an earlier one that read better.

`make snapshot` is the one cookbook command on this path that spends credit: `make refresh`, `make previews`, `make render` and every check the pull request asks for spend none. Its run is also the method's smoke proof, since the snapshot is refused unless the output has its contract's shape. Take a new snapshot whenever a change alters what the method returns.

## 6. The page

1. Add the method's entry under `[methods.<name>]` in `cookbook.toml`, above its sample records: the `title` and the `pitch` the page opens with, the `app_dir` the app initializer creates, the `yours_dir` "Make it yours" copies the method into, and the `yours_change` it asks for, which should be the change the person's company would make first, such as its own criteria. Leave out `chatbot` unless the default sentence reads wrong. When the contract cannot say how the output reads, add the hints under `[methods.<name>.output]`: `formats` for a text field holding Markdown or HTML, and `item_label` for the items of a list output ([README.md](README.md#cookbooktoml) gives every field and its default).
2. `make render` writes `methods/<name>/README.md`, the page's TypeScript and Python snippets as files under `tests/snippets/<name>/`, each reading the output through the types `make refresh` generated beside it, and the front page's list of methods. If a bundle changed since the proof, run `make refresh` first, and take a new snapshot if what the method returns changed too.
3. Read the page as a prospect would. It opens with the pitch; "The sample" shows the input, a PDF document by its first-page preview, with its source and licence, or says it is fictional; "What you get" gives the run's date and shows the output as the deliverable the sketch drew; then come "Takes", "Returns" and the doors. When the output does not read as the sketch, fix the hints, or go back to the build.

Commit the method together: its package with its snapshot and any `output/`, its sample under `assets/<name>/` with its preview, its entry and records in `cookbook.toml`, its page, everything under `tests/snippets/<name>/`, generated types included, and the front page `README.md`.

## 7. The pull request

1. Add the method to `RIGHT_OUTPUTS` in `tests/tooling/test_data.py`: a hand-built output of its contract's shape, written from the one the method returned, since the tests hold every method to one and fail on a method without it.
2. `make agent-check` and `make agent-test`: the linters, the pages and snippets against a fresh render, which also holds each snapshot to its contract, its files and its sample, the lockstep versions and the tests.
3. `make check-cookbook`, which is what CI runs on your pull request: it adds the links, where the new sample is reported as not published, the library's snapshot, and `make check-recipe-types`, which type-checks the page's snippet files against the SDK and the method's generated types, each in its own environment.
4. `make check-hosted`, by hand, since CI holds no key: every package validates on production and its contract is current, and every address validates, the new method's being reported as not released until the next release carries it. It spends nothing.
5. An entry in `CHANGELOG.md` under `## [Unreleased]`, in `### Added`, naming the method's title and what it shows, in the file's own style.

**The smoke check keeps it working.** `make check-smoke METHOD=<name>` runs the method once more on production on its sample and checks that its output has its contract's shape, which is what keeps every method working once it has landed. It spends credit, and nothing starts it by itself. You need not run it for a new method, since the snapshot run has already proved the same thing.

Open the pull request against `dev`, as [CONTRIBUTING.md](../CONTRIBUTING.md) says. The method resolves by address once the next release brings it to `main`, and the release re-renders every page at its tag.
