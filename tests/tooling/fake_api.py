"""A stand-in for production, answering the tooling's calls through `httpx.MockTransport` so that no test reaches the network."""

import json
from typing import Any, cast

import httpx

from scripts.hosted import HostedClient

FAKE_API_KEY = "not-a-real-key"
FAKE_BASE_URL = "https://api.example.invalid"


class FakeApi:
    """Answers each call from the answers queued for its method and path, and records every request.

    The last answer queued for a route repeats, so one `202` keeps a run going for as long as it is asked. A call with no answer queued fails
    the test, naming the route.
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self._answers: dict[tuple[str, str], list[httpx.Response]] = {}

    def answer(self, method: str, path: str, *responses: httpx.Response) -> None:
        self._answers.setdefault((method, path), []).extend(responses)

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        queue = self._answers.get((request.method, request.url.path))
        if not queue:
            msg = f"the fake API has no answer for {request.method} {request.url.path}"
            raise AssertionError(msg)
        return queue.pop(0) if len(queue) > 1 else queue[0]

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    @property
    def client(self) -> HostedClient:
        return HostedClient(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL, transport=self.transport)

    def calls(self) -> list[str]:
        """Every call made so far, as `METHOD path`."""
        return [f"{request.method} {request.url.path}" for request in self.requests]

    def bodies(self, method: str, path: str) -> list[dict[str, Any]]:
        """The JSON bodies of the calls made to one route, in order."""
        return [
            cast("dict[str, Any]", json.loads(request.content)) for request in self.requests if request.method == method and request.url.path == path
        ]
