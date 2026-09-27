# Copy a method, change it, and make it yours

A published method is a starting point. Your coding agent copies it at its tag, changes it, proves the change on the method's own sample and saves it to your Pipelex account, where it gets an id of its own, `mt_…`. From then on, your chatbot, your code and your app take that id where they took the address. This recipe does it with the cookbook's [document question answering](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/answer_from_documents) method, which answers a question from a set of documents and quotes the passages its answer rests on, on its sample: the European Commission's guidelines on the definition of an AI system under the AI Act, and a question a customer support team asks about a tool of its own. The change keeps what the method takes and returns: answer in the language the question is asked in. The method's page suggests another change, which adds to what the method returns and so is design work, as [the page's promise](#how-it-is-built) explains.

It shows what making a method yours involves today:

- **A copy starts at a tag.** The agent takes the package from the cookbook's repository at `v0.20.0`, so what you change is exactly what the address `github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0` runs.
- **A change that keeps the contract is an edit.** `/pipelex-edit` rewrites prompts, models and wording itself, and validates the method before and after. A change to what the method takes or returns is design work, which it hands to `/pipelex-design`.
- **A save is a deployment.** `/pipelex-catalog` saves the directory as a new method in your organization's catalog, and the saved method keeps no record of the address it came from: no gesture yet saves a published method into your account in one step.
- **A run proves the change, and the document proves the answer.** Asked in French, the method answered, explained and gave its reasons in French, while every quote stayed in the guidelines' English; asked in English by its id, it answered in English. Whether an answer is right is read in the document itself: both runs answered no, as the guidelines' own example of a customer support system that predicts the mean resolution time from past data bears out. The runs prove the change, not the method.

## What it needs

- Claude Code or Codex with the Pipelex plugin and your Pipelex API key, set up as the plugin's [quick start](https://github.com/Pipelex/pipelex-plugins#quick-start) says, started in the directory the copy goes into: the plugin's tools read and write files in the directory your agent was started in.
- `git`, which the agent uses to take the package at its tag.
- Credit on your Pipelex account: each run is one run on the hosted API. Validating, editing and saving spend none.

## Run it

In the directory of your choice, ask your agent, in the words of the request the method's page gives, with this recipe's change and the question you want to prove it on:

> Copy github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.20.0 into ./document-qa, have it answer in the language of the question, prove it on the sample with the question asked in French, and save it to my Pipelex account as "document-qa".

The agent reports each step as it goes, and says before the run that it spends credit. Then, from a session in the same directory with a key of the same organization, run the saved method by its id:

> Run mt_… on its sample.

The agent finds the sample in `document-qa/inputs.json`, beside the bundle that `pipelex-method.json` links to the id, and asks its question as the sample gives it, in English.

### Point every door at the id

- **Your chatbot**, signed in to the organization your key belongs to: ask "What methods do I have?", and the Pipelex connector lists `document-qa` among them, shows it and runs it. The connector runs on your sign-in and the plugin on your key, so a method saved from one is visible from the other only when both use the same organization.
- **Your code**: pass the id as `method_id` where the snippets on the method's page pass `method_ref`, `client.start_and_wait(method_id="mt_…", inputs=…)` in Python and `client.startAndWaitForResult({ method_id: "mt_…", inputs })` in TypeScript. Your catalog is not versioned: a later save changes what the id runs.
- **Your app**: `make add-method METHOD=mt_…` in an app made from the method-app template adds it as a tab, as the [second-tab recipe](../../app/second-tab/) does with an address, and `npm create @pipelex/method-app@latest document-qa-app -- --method mt_…` makes an app for it alone.

## What you get

The agent copies the package with git, at the tag, and keeps only the method's directory:

```bash
git clone --depth 1 --branch v0.20.0 --filter=blob:none --sparse https://github.com/Pipelex/pipelex-cookbook.git cookbook-clone
git -C cookbook-clone sparse-checkout set methods/answer_from_documents
mkdir -p document-qa
cp -R cookbook-clone/methods/answer_from_documents/. document-qa/
rm -rf cookbook-clone
```

`/pipelex-edit` says what it will change, then reports it:

```text
I'll make a prompt-only edit of document-qa/bundle.mthds: the retrieve_passages and synthesize_answer system prompts will write their prose in the question's language and never translate a quote, so what the method takes and returns does not change.

I changed document-qa/bundle.mthds so the method answers in the language the question is asked in. Only two system prompts changed. synthesize_answer now writes the answer, the explanation, the caveats and every contradiction noted in the question's language, a yes or no included, while the status and confidence codes, the 'Not answerable' sentinel and the quoted passages stay as they are. retrieve_passages gains an eleventh rule: each passage's relevance reasoning is written in the question's language, and a quote is never translated. The inputs and the output concept are unchanged, so the method's contract is the same. Validation passed before and after the edit on all six pipes: "All pipes are concretely implemented — no PipeSignature placeholders remain. Strict validation will pass; this method is runnable." Next, as you asked, I prove it on the sample with /pipelex-run, then save it with /pipelex-catalog.
```

For the run from the files, on the [sample guidelines](https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/assets/answer_from_documents/ai_system_definition_guidelines.pdf), the agent put the sample's question into French:

> Notre équipe de support client veut que chaque nouveau ticket affiche un délai de résolution estimé, calculé comme la moyenne des délais de résolution des tickets passés de la même catégorie. Cet outil est-il un système d'IA au sens de l'AI Act ?

It reported the run's id as soon as the run started, and the results once it completed:

```text
Run run_… completed in about 75 seconds, for $0.35 across 5 model calls. The change took: the method answered in French, and every quote stayed in the guidelines' English.

status: answered · confidence: high · answer: Non

Si l’outil se borne à calculer, pour la catégorie du nouveau ticket, la moyenne historique des délais de résolution, il relève d’une estimation statique fondée sur une règle statistique élémentaire, et non d’un système d’IA. Les lignes directrices citent presque exactement les systèmes de support client prédisant le délai moyen de résolution à partir de données passées parmi les exemples hors du champ de la définition. Le fait que le résultat soit présenté comme une prédiction ne suffit pas : la capacité d’inférence est une condition indispensable, destinée à distinguer les systèmes d’IA des logiciels traditionnels exécutant des règles définies par des personnes.

Supporting passages, all from the Commission Guidelines on the definition of an AI system, C(2025) 5053 final, quoted in English with their relevance reasoning in French:
- p. 2, ¶8–9: the definition in Article 3(1) and its seven elements.
- p. 5, ¶26–27: the capability to infer is indispensable.
- p. 9, ¶46: basic data processing, whose examples include software that calculates a population average.
- p. 10, ¶49–51: "Static estimation systems, such as customer support response time system that are based on static estimation to predict the mean resolution time from the past data …", with the reasoning "Ce passage vise presque exactement le cas posé et place les systèmes statiques de support client prédisant un délai moyen à partir des données passées hors du champ de la définition."
- p. 12, ¶61–62: the architecture and functionality of the system decide.

Contradictions noted: none.

Caveats: Cette conclusion suppose que l’outil se limite réellement à une moyenne arithmétique prédéfinie par catégorie. Si la catégorie est inférée par apprentissage automatique, si l’outil dérive un modèle ou un algorithme des données, traite des relations complexes, ou comporte d’autres fonctions d’IA, la qualification pourrait changer. L’appréciation définitive dépend donc de son architecture et de ses fonctionnalités concrètes.

I saved the run to runs/run_…/main_stuff.json. Next, as you asked, I save the method to your Pipelex account as "document-qa".
```

That is the right answer: under "Simple prediction systems", on the page the guidelines number 10, paragraph 49 places outside the definition the systems whose performance a basic statistical learning rule can achieve, and paragraph 51 gives as one of them a customer support system that predicts the mean resolution time from past data. Every quote is the guidelines' own text on the page it cites, except that the first passage opens with paragraph 8's lead-in sentence, which ends page 1.

`/pipelex-catalog` says what it is about to do, saves it and reports its id:

```text
Creating a new method **document-qa** on Pipelex from `document-qa/`.

Saved: created document-qa as mt_… on api.pipelex.com, updated_at 2026-09-27T09:01:48.928291+00:00. The workshop linked the directory with document-qa/pipelex-method.json: commit it with the method, so that the next save from this directory, or a teammate's, updates this method instead of creating a second one. From now on your chatbot, your code and your app can run it by that id.
```

The run by the id, with the question in English as the sample gives it, answered in English:

```text
Run run_… of document-qa completed in about 75 seconds, for $0.40 across 5 model calls. Asked in English, it answered in English.

status: answered · confidence: high · answer: No

Assuming the tool only applies a fixed or static category-level arithmetic mean from past tickets, the Commission Guidelines treat it as outside the AI-system definition. Although it produces a prediction-like output, the decisive element is the capability to infer; basic data processing and basic statistical methods that merely calculate historical averages without learning, reasoning, modelling, or AI techniques do not meet that element. The Guidelines give a nearly identical example: a customer-support response-time system that predicts mean resolution time from past data as a static baseline.

Supporting passages, all from the Commission Guidelines on the definition of an AI system, C(2025) 5053 final:
- p. 2: the definition in Article 3(1).
- p. 5, ¶26: the capability to infer is indispensable.
- p. 9, ¶46: basic data processing, whose examples include software that calculates a population average.
- p. 10, ¶49, ¶50 and ¶51: a basic statistical learning rule falls outside the definition, a mean baseline is not sophisticated inference, and "customer support response time system that are based on static estimation to predict the mean resolution time from the past data" is one of the examples.
- p. 12, ¶61: the architecture and functionality of the system decide.
- p. 1, ¶7: the Guidelines are not binding.

Contradictions noted: none.

Caveats: This conclusion assumes the tool does nothing beyond a fixed or static arithmetic mean for a category. Classification could change if categories are assigned by an AI model, the estimate is weighted or adjusted using additional variables, or the system uses machine learning, logic- or knowledge-based inference, modelling, pattern analysis, or adaptive updating. Automatic generation and display may satisfy machine-based operation, some autonomy, an objective, a prediction-like output, and influence on a virtual environment, but those features do not replace the indispensable inference element. The Commission Guidelines are non-binding, and authoritative interpretation ultimately belongs to the CJEU.

I saved the run to runs/run_…/main_stuff.json.
```

That is right too, on the same paragraphs 49 and 51, and every passage it quotes is on the page it cites, down to paragraph 7 on page 1, which makes the guidelines non-binding, as its caveats say. How often the method answers right is a question for more cases than one sample, which is what `/pipelex-lab` measures, as the [design-from-a-sentence recipe](../design-from-a-sentence/) shows.

Adding it to the DPE app of the [deployed-app recipe](../../app/deployed-app/) by its id, as a dry run with `make add-method METHOD=mt_… DRY_RUN=1`, shows what the tab would be, what it would write, and what an id is bound to:

```text
add-method: method_id mt_…, via https://api.pipelex.com
  pipe:   document_qa.answer_from_documents
  output: document_qa.DocumentAnswer
  files:  documents[]
  entry:  "document-qa" (id document-qa)

Would write:
  methods/document-qa/method.json
  src/generated/document-qa/  (types.ts, binder.ts, contracts.ts, codegen.lock, sources.json)
  src/types/documentQaPipeline.ts
  src/types/documentQaUploads.ts
  src/actions/runDocumentQaPipeline.ts
  src/actions/runDocumentQaPipeline.test.ts
  src/components/DocumentQaForm.tsx
  src/methods.ts  (one import, one entry)

! a method_id is scoped to your key's organization, so `npm run codegen` on this slice needs a key of that same org. A published address (method_ref) is the portable form.

Nothing was written (--dry-run).
```

## How it is built

The recipe is a request to your agent, so it carries no code: the Pipelex plugin's skills do the work through the Pipelex tools.

- **The copy.** No skill copies a published method: `/pipelex-edit` and `/pipelex-design` refuse an address, since a published method is not theirs to change. So the agent takes the package with git, at the tag the address names. The copy keeps the package's `METHODS.toml` and `README.md` as the cookbook wrote them, still naming the cookbook's address: edit them before you publish the package yourself.
- **The change.** [`/pipelex-edit`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-edit/SKILL.md) validates every `.mthds` file with `mthds_validate` before it changes anything, applies the change, and validates again. It applies a change that keeps what the method takes and returns, and hands anything that changes them to `/pipelex-design`.
- **The proof.** [`/pipelex-run`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-run/SKILL.md) checks the inputs against the method's input template (`mthds_inputs_template`) and validates the method before any credit is spent, then runs it from its files with `mthds_run`, on the package's own `inputs.json` with the question in the language you asked for, and later by its id with `method_id`. It follows each run with `mthds_run_status`, reads its output with `mthds_run_results` and saves it to `runs/<run_id>/` with `mthds_download_artifacts`.
- **The save.** [`/pipelex-catalog`](https://github.com/Pipelex/pipelex-plugins/blob/main/pipelex/skills/pipelex-catalog/SKILL.md) sends the directory's `.mthds` files with `mthds_save_method`, root file first, takes the name from your request or asks for one when the method is new, and writes `pipelex-method.json` beside the root file, which links the directory to the method so that the next save updates it rather than creating another. Commit that file with the method. The link is written only when the plugin's tools can read the directory, which they can when your agent was started in it or above it.
- **The page's promise.** Every method page's "Make it yours" section gives a request of the shape this recipe starts from, with a change suited to that method. Most of those changes reshape what the method returns, as the one on this method's page does by adding whether the answer goes to counsel, so for them `/pipelex-edit` hands over to `/pipelex-design`. This recipe makes a change that keeps the contract instead, to show the edit itself.
