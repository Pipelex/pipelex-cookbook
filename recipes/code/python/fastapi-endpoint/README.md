# A FastAPI endpoint typed by the method it runs

Your service needs to answer questions from documents: a contract, a report, a manual. This recipe is a FastAPI app with one endpoint, `POST /answers`, that runs the cookbook's [document question answering](../../../../methods/answer_from_documents/) method by its address and answers with the method's own result.

It shows how a method becomes part of an API:

- **The method's types are the endpoint's types.** The response embeds `DocumentAnswer`, the model generated from the method, so FastAPI validates every answer against it and documents its fields at `/docs`, down to each quoted passage and its page number.
- **One client for the app.** The `PipelexAPIClient` opens when the app starts and closes when it stops, and each request borrows it through a dependency.
- **Failures in HTTP terms.** A run that fails answers 502 with the reason, and a run still going when the wait ends answers 504 with its id, since the run carries on server-side.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each question is one run on the hosted API and spends credit.

## Run it

```bash
export PIPELEX_API_KEY=…
uv run app.py
```

Then, from another terminal, ask the method's sample question about a Pew Research Center report:

```bash
curl -s -X POST http://127.0.0.1:8000/answers \
  -H 'Content-Type: application/json' \
  -d '{"documents": ["https://huggingface.co/datasets/yubo2333/MMLongBench-Doc/resolve/main/documents/PH_2016.06.08_Economy-Final.pdf"], "question": "Among all 12 references in this report, how many are from its own research center?"}'
```

The request takes `documents`, a list of links the hosted API can fetch, a `question`, and an optional `context` that helps read the question and is never cited. The interactive documentation at http://127.0.0.1:8000/docs lets you try it from the browser.

## What you get

A JSON body with the `answer` and the `run_id` that produced it. On the sample question, `answer.status` is `answered`, `answer.answer` is `8`, and `answer.supporting_passages` quotes the report's references with their page numbers. The answer also carries its `confidence`, its `caveats` and any contradictions it noticed between documents.

## Before you deploy it

The app has no authentication of its own, and every question it answers is a run on your key's credit. Run as above, it listens on `127.0.0.1` only, so nothing but your own machine reaches it. Served any other way, for instance with `uvicorn app:app --host 0.0.0.0`, anyone who reaches it spends your credit and has the hosted API fetch links of their choosing. Put it behind your service's own authentication and rate limits before it faces a network: a FastAPI [security dependency](https://fastapi.tiangolo.com/tutorial/security/) on the route, or the gateway your other services sit behind. The request already refuses more than ten documents at once.

## How it is built

- `app.py` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.18.0`, pinned to a release tag so the method never changes under the types.
- `generated/answer_from_documents/` holds those types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- A long document set can take minutes to answer. An endpoint that should answer at once starts the run with `client.start(...)`, returns its id, and lets the caller fetch the result later with `client.get_run_result(...)`.
