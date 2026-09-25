# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0", "fastapi>=0.115", "uvicorn>=0.30"]
# ///
"""An HTTP endpoint that answers a question from documents, typed end to end by the method it runs.

`POST /answers` takes links to documents and a question. The endpoint runs the cookbook's document question answering
method by its address and answers with the method's own result, typed by the `DocumentAnswer` model generated from the
method: FastAPI validates every response against it and documents it at `/docs`.

    uv run app.py        # serves http://127.0.0.1:8000, with the API's documentation at /docs

`PIPELEX_API_KEY` must be set; each question is one run on the hosted API and spends credit.
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
from pydantic import BaseModel, Field, HttpUrl

from generated.answer_from_documents.models import DocumentAnswer

METHOD_REF = "github.com/Pipelex/pipelex-cookbook/answer_from_documents@v0.18.0"


class AnswerRequest(BaseModel):
    documents: list[HttpUrl] = Field(min_length=1, description="Links to the documents to answer from, each one the hosted API can fetch")
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
    except RunTimeoutError as exc:
        # The run carries on server-side: its id is what a caller would resume it by.
        raise HTTPException(status_code=504, detail=f"The run {exc.run_id} is still going; ask again later.") from exc
    except (PipelineRequestError, httpx.HTTPStatusError) as exc:
        raise HTTPException(status_code=502, detail=f"The method could not answer: {exc}") from exc
    return AnswerResponse(answer=DocumentAnswer.model_validate(results.main_stuff), run_id=results.pipeline_run_id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
