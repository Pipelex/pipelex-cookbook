# Copy a method, change it, and make it yours

A published method is a starting point. Your coding agent copies it at its tag, changes it, proves the change on the method's own sample and saves it to your Pipelex account, where it gets an id of its own, `mt_…`. From then on, your chatbot, your code and your app take that id where they took the address. This recipe does it with the cookbook's [document question answering](../../../methods/answer_from_documents/) method, which answers a question from a set of documents and quotes the passages its answer rests on. The change is the one its page suggests: answer in the language the question is asked in.

It shows what making a method yours involves today:

- **A copy starts at a tag.** The agent takes the package from the cookbook's repository at `v0.18.0`, so what you change is exactly what the address `github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.18.0` runs.
- **A change that keeps the contract is an edit.** `/pipelex-edit` rewrites prompts, models and wording itself, and validates the method before and after. A change to what the method takes or returns is design work, which it hands to `/pipelex-design`.
- **A save is a deployment.** `/pipelex-catalog` saves the directory as a new method in your organization's catalog, and the saved method keeps no record of the address it came from: no gesture yet saves a published method into your account in one step.
- **One run proves the change, not the method.** A run shows the change took, and the method's answer key says whether the answer is right. On this sample, one of the two runs miscounted, and the key is how you tell.

## What it needs

- Claude Code or Codex with the Pipelex plugin and your Pipelex API key, set up as the plugin's [quick start](https://github.com/Pipelex/pipelex-plugins#quick-start) says, started in the directory the copy goes into: the plugin's tools read and write files in the directory your agent was started in.
- `git`, which the agent uses to take the package at its tag.
- Credit on your Pipelex account: each run is one run on the hosted API. Validating, editing and saving spend none.

## Run it

In the directory of your choice, ask your agent, as the method's page says, with the question you want to prove it on:

> Copy github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.18.0 into ./document-qa, have it answer in the language of the question, prove it on the sample with the question asked in French, and save it to my Pipelex account as "document-qa".

The agent reports each step as it goes, and says before the run that it spends credit. Then, from any session with a key of the same organization, run the saved method by its id:

> Run mt_… on its sample with the question: Among all 12 references in this report, how many are from its own research center?

### Point every door at the id

- **Your chatbot**, signed in to the organization your key belongs to: ask "What methods do I have?", and the Pipelex connector lists `document-qa` among them, shows it and runs it. The connector runs on your sign-in and the plugin on your key, so a method saved from one is visible from the other only when both use the same organization.
- **Your code**: pass the id as `method_id` where the snippets on the method's page pass `method_ref`, `client.start_and_wait(method_id="mt_…", inputs=…)` in Python and `client.startAndWaitForResult({ method_id: "mt_…", inputs })` in TypeScript. Your catalog is not versioned: a later save changes what the id runs.
- **Your app**: `make add-method METHOD=mt_…` in an app made from the method-app template adds it as a tab, as the [second-tab recipe](../../app/second-tab/) does with an address, and `npm create @pipelex/method-app@latest document-qa-app -- --method mt_…` makes an app for it alone.

## What you get

The agent copies the package with git, at the tag, and keeps only the method's directory:

```bash
git clone --depth 1 --branch v0.18.0 --filter=blob:none --sparse https://github.com/Pipelex/pipelex-cookbook.git cookbook-clone
git -C cookbook-clone sparse-checkout set methods/answer_from_documents
mkdir -p document-qa
cp -R cookbook-clone/methods/answer_from_documents/. document-qa/
rm -rf cookbook-clone
```

`/pipelex-edit` says what it will change, then reports it:

```text
I changed document-qa/bundle.mthds so the method answers in the language the question is asked in. Only two system prompts changed. synthesize_answer now writes the answer, the explanation, the caveats and the noted contradictions in the question's language, while the status and confidence codes, the 'Not answerable' sentinel and the quoted passages stay as they are. retrieve_passages now writes each passage's relevance reasoning in the question's language and never translates a quote. The inputs and the output concept are unchanged, so the method's contract is the same. The bundle was valid and runnable before the edit and still is after it, with no pending signatures.
```

The run from the files, on the [sample report](https://huggingface.co/datasets/yubo2333/MMLongBench-Doc/resolve/main/documents/PH_2016.06.08_Economy-Final.pdf) with the question in French, took about a minute and answered in French, with the quotes kept in the report's English:

```text
status: answered · confidence: high · answer: 8

Le rapport est rattaché au Pew Research Center. Parmi les 12 références des pages 21 et 22, cinq références de la page 21 et trois de la page 22 sont attribuées au Pew Research Center, soit huit au total.
```

That is what the method's [answer key](../../../methods/answer_from_documents/key.md) asks for: 8, answered, from the report's references appendix.

`/pipelex-catalog` saves it and reports its id:

```text
Saved: created document-qa as mt_… on api.pipelex.com.
```

The run by the id, with the question in English, answered in English, and miscounted:

```text
status: answered · confidence: high · answer: 9

Pew Research Center is identified as the report's own research center. Of the 12 references across pages 21–22, nine are authored or published by Pew Research Center and three are from other institutions.
```

The key says 8, so this run fails it. Both runs counted six of page 21's references as Pew's where the page shows five, and only the first caught it when writing the answer. A change is proven on one run; whether the method answers right is a question for several runs against the key, which is what `/pipelex-lab` does, as the [design-from-a-sentence recipe](../design-from-a-sentence/) shows.

Adding it to the DPE app of the [deployed-app recipe](../../app/deployed-app/) by its id, as a dry run, shows what the tab would be, and what an id is bound to:

```text
add-method: method_id mt_…, via https://api.pipelex.com
  pipe:   document_qa.answer_from_documents
  output: document_qa.DocumentAnswer
  files:  documents[]
  entry:  "document-qa" (id document-qa)

! a method_id is scoped to your key's organization, so `npm run codegen` on this slice needs a key of that same org. A published address (method_ref) is the portable form.
```

## How it is built

The recipe is a request to your agent, so it carries no code: the Pipelex plugin's skills do the work through the Pipelex tools.

- **The copy.** No skill copies a published method: `/pipelex-edit` and `/pipelex-design` refuse an address, since a published method is not theirs to change. So the agent takes the package with git, at the tag the address names. The copy keeps the package's `METHODS.toml`, `README.md` and `key.md` as the cookbook wrote them, still naming the cookbook's address: edit them before you publish the package yourself.
- **The change.** [`/pipelex-edit`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-edit/SKILL.md) validates every `.mthds` file with `mthds_validate` before it changes anything, applies the change, and validates again. It applies a change that keeps what the method takes and returns, and hands anything that changes them to `/pipelex-design`.
- **The proof.** [`/pipelex-run`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-run/SKILL.md) runs the method from its files with `mthds_run`, on the package's own `inputs.json` and the question you gave, then by its id with `method_id`.
- **The save.** [`/pipelex-catalog`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-catalog/SKILL.md) sends the directory's `.mthds` files with `mthds_save_method`, root file first, asks for a name when the method is new, and writes `pipelex-method.json` beside the root file, which links the directory to the method so that the next save updates it rather than creating another. Commit that file with the method. The link is written only when the plugin's tools can read the directory, which they can when your agent was started in it or above it.
- **The page's promise.** Every method page's "Make it yours" section gives the request this recipe starts from, with a change suited to that method. Most of those changes reshape what the method returns, so for them `/pipelex-edit` hands over to `/pipelex-design`.
