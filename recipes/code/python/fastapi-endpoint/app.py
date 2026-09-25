# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0", "fastapi>=0.115", "uvicorn>=0.30", "mthds>=0.15", "httpx>=0.25", "pydantic>=2.10.6"]
# ///
"""An HTTP endpoint that answers a question from documents, typed end to end by the method it runs.

`POST /answers` takes links to documents and a question. The endpoint runs the cookbook's document question answering
method by its address and answers with the method's own result, typed by the `DocumentAnswer` model generated from the
method: FastAPI validates every response against it and documents it at `/docs`.

    uv run app.py        # serves http://127.0.0.1:8000, with the API's documentation at /docs

`PIPELEX_API_KEY` must be set; each question is one run on the hosted API and spends credit. The app has no
authentication of its own: every caller who reaches it spends your key's credit, so it listens on 127.0.0.1 only, and
a deployment puts it behind your service's own authentication and rate limits.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from mthds.protocol.exceptions import PipelineRequestError
from pipelex_sdk.client import PipelexAPIClient
from pipelex_sdk.errors import RunTimeoutError
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from generated.answer_from_documents.models import DocumentAnswer

METHOD_REF = "github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.18.0"
MAX_DOCUMENTS = 10


class AnswerRequest(BaseModel):
    documents: list[HttpUrl] = Field(
        min_length=1, max_length=MAX_DOCUMENTS, description="Links to the documents to answer from, each one the hosted API can fetch"
    )
    question: str = Field(min_length=1, description="The question to answer from the documents")
    context: str | None = Field(default=None, description="Background that helps read the question, never cited as a source")


class AnswerResponse(BaseModel):
    answer: DocumentAnswer
    run_id: str = Field(description="The run that answered, to find it again in your Pipelex account")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """One client for the whole life of the app, reading `PIPELEX_API_KEY` once, instead of one per request."""
    async with PipelexAPIClient() as client:
        app.state.pipelex_client = client
        yield


def pipelex_client(request: Request) -> PipelexAPIClient:
    client: PipelexAPIClient = request.app.state.pipelex_client
    return client


app = FastAPI(title="Answers from documents", lifespan=lifespan)


@app.post("/answers")
async def answer(body: AnswerRequest, client: Annotated[PipelexAPIClient, Depends(pipelex_client)]) -> AnswerResponse:
    """Answer the question from the documents, quoting the passages the answer rests on."""
    inputs: dict[str, Any] = {"documents": [{"url": str(url)} for url in body.documents], "question": body.question}
    if body.context:
        inputs["context"] = body.context
    try:
        results = await client.start_and_wait(method_ref=METHOD_REF, inputs=inputs)
        document_answer = DocumentAnswer.model_validate(results.main_stuff)
    except RunTimeoutError as exc:
        # The run carries on server-side: its id is what a caller would resume it by.
        raise HTTPException(status_code=504, detail=f"The run {exc.run_id} is still going; ask again later.") from exc
    except (PipelineRequestError, httpx.HTTPError, ValidationError) as exc:
        # A refused or failed run, a hosted API that cannot be reached, or an answer the generated types do not accept.
        raise HTTPException(status_code=502, detail=f"The method could not answer: {exc}") from exc
    return AnswerResponse(answer=document_answer, run_id=results.pipeline_run_id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
