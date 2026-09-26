import base64
from datetime import UTC, datetime
from itertools import count
from typing import Any

import httpx
import pytest
from pytest_mock import MockerFixture

from scripts.cookbook import Cookbook, load_cookbook
from scripts.exceptions import CookbookLayoutError, HostedApiError, HostedRunError, HostedRunTimeoutError
from scripts.hosted import (
    POLL_INTERVAL_SECONDS,
    HostedClient,
    RunRoute,
    StorageUrlError,
    download,
    run_address,
    run_package,
    upload_local_samples,
)
from tests.tooling.fake_api import FAKE_API_KEY, FAKE_BASE_URL, FakeApi
from tests.tooling.test_data import WIDGETS_BUNDLE, WIDGETS_SAMPLE_URL, WORDS_BUNDLE, MakeCookbook

START = "/v1/start"
UPLOAD = "/v1/upload"
RESOLVE = "/v1/resolve-storage-url/bulk"
RUN_ID = "run_0123"
RESULTS = f"/v1/runs/{RUN_ID}/results"
STATUS = f"/v1/runs/{RUN_ID}/status"
SAMPLE_PATH = "assets/extract_widgets/catalogue.png"
SAMPLE_BYTES = b"\x89PNG a catalogue page"
UPLOADED_URI = "pipelex-storage://org_1/assets/5f0c.png"
ADDRESS = "github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0"
OUTPUT: dict[str, Any] = {"widgets": [{"name": "Bracket", "colour": "red"}]}
# Two priced calls and one whose model has no rate table.
USAGES: list[dict[str, Any]] = [
    {"model_type": "llm", "inference_model_name": "model-a", "cost": 0.0125},
    {"model_type": "extract", "inference_model_name": "model-b", "cost": None},
    {"model_type": "llm", "inference_model_name": "model-a", "cost": 0.0075},
]
STATUS_BODY: dict[str, Any] = {
    "pipeline_run_id": RUN_ID,
    "status": "COMPLETED",
    "created_at": "2026-09-26T12:00:00+02:00",
    "finished_at": "2026-09-26T10:00:42Z",
}
STORAGE_LINK = "https://bucket.example.invalid/org_1/results/out.png?X-Amz-Signature=do-not-print"


def _cookbook_with_sample(make_cookbook: MakeCookbook) -> Cookbook:
    """The fixture cookbook, with the widgets sample its inputs link on `main` held in the checkout."""
    root = make_cookbook()
    sample = root / SAMPLE_PATH
    sample.parent.mkdir(parents=True)
    sample.write_bytes(SAMPLE_BYTES)
    return load_cookbook(root)


def _started(provenance: dict[str, Any] | None = None) -> httpx.Response:
    return httpx.Response(202, json={"pipeline_run_id": RUN_ID, "state": "STARTED", "method_provenance": provenance})


def _completed(main_stuff: Any = None, usages: list[dict[str, Any]] | None = None) -> httpx.Response:
    return httpx.Response(200, json={"pipeline_run_id": RUN_ID, "main_stuff": main_stuff, "tokens_usages": usages})


class TestRunClient:
    def test_a_package_runs_from_its_files_on_its_sample_uploaded_from_the_checkout(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        sleep = mocker.patch("scripts.hosted.sleep")
        cookbook = _cookbook_with_sample(make_cookbook)
        fake_api.answer("POST", UPLOAD, httpx.Response(200, json={"uri": UPLOADED_URI, "filename": "catalogue.png"}))
        fake_api.answer("POST", START, _started())
        fake_api.answer(
            "GET",
            RESULTS,
            httpx.Response(202, headers={"Retry-After": "7"}, json={"state": "RUNNING"}),
            httpx.Response(503, headers={"Retry-After": "1"}, json={"detail": "The run store is degraded."}),
            _completed(OUTPUT, USAGES),
        )
        fake_api.answer("GET", STATUS, httpx.Response(200, json=STATUS_BODY))

        run = run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[1])

        assert fake_api.calls() == [f"POST {UPLOAD}", f"POST {START}", f"GET {RESULTS}", f"GET {RESULTS}", f"GET {RESULTS}", f"GET {STATUS}"]
        assert all(request.headers["Authorization"] == f"Bearer {FAKE_API_KEY}" for request in fake_api.requests)
        assert fake_api.bodies("POST", UPLOAD) == [
            {"filename": "catalogue.png", "data": base64.b64encode(SAMPLE_BYTES).decode("ascii"), "content_type": "image/png"}
        ]
        # The bundle's own `main_pipe` names the pipe: the start names none.
        assert fake_api.bodies("POST", START) == [
            {"mthds_contents": [WIDGETS_BUNDLE], "inputs": {"catalogue": {"concept": "widgets.CataloguePage", "content": {"url": UPLOADED_URI}}}}
        ]
        # The first wait is the seven seconds the API asked for, the second the poll interval, which a shorter `Retry-After` does not shorten.
        assert [call.args[0] for call in sleep.call_args_list] == [7, POLL_INTERVAL_SECONDS]
        assert (run.run_id, run.base_url, run.route, run.method_ref, run.commit_sha) == (RUN_ID, FAKE_BASE_URL, RunRoute.FILES, None, None)
        assert (run.started_at, run.finished_at) == (datetime(2026, 9, 26, 10, 0, 0, tzinfo=UTC), datetime(2026, 9, 26, 10, 0, 42, tzinfo=UTC))
        assert run.main_stuff == OUTPUT
        assert run.cost_usd is not None
        assert abs(run.cost_usd - 0.02) < 1e-12
        assert run.summary() == f"run {RUN_ID}, $0.0200, 42 s"

    def test_an_address_runs_at_its_tag_and_records_the_commit_it_resolved_to(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        provenance = {"address": "github.com/Pipelex/pipelex-cookbook/count_words", "tag": "v0.9.0", "commit_sha": "42dcaa9a"}
        fake_api.answer("POST", START, _started(provenance))
        fake_api.answer("GET", RESULTS, _completed({"text": "four words"}))
        fake_api.answer("GET", STATUS, httpx.Response(200, json=STATUS_BODY))

        run = run_address(client=fake_api.client, cookbook=cookbook, address=ADDRESS, inputs={"text": "The quick brown fox"})

        assert fake_api.bodies("POST", START) == [{"method_ref": ADDRESS, "inputs": {"text": "The quick brown fox"}}]
        assert (run.route, run.method_ref, run.commit_sha, run.main_stuff) == (RunRoute.ADDRESS, ADDRESS, "42dcaa9a", {"text": "four words"})
        # The results relayed no usage records, so the cost is unknown rather than nothing.
        assert run.cost_usd is None
        assert run.summary() == f"run {RUN_ID}, cost unknown, since the run relayed no usage records, 42 s"

    def test_every_sample_into_this_repository_is_uploaded_once_whatever_its_ref(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = _cookbook_with_sample(make_cookbook)
        fake_api.answer("POST", UPLOAD, httpx.Response(200, json={"uri": UPLOADED_URI, "filename": "catalogue.png"}))
        at_a_tag = WIDGETS_SAMPLE_URL.replace("/main/", "/v0.9.0/")
        elsewhere = "https://example.org/catalogue.pdf"
        note = f"The catalogue is at {WIDGETS_SAMPLE_URL}"

        prepared = upload_local_samples(
            client=fake_api.client,
            cookbook=cookbook,
            inputs={
                "pages": {"concept": "widgets.CataloguePage", "content": [{"url": WIDGETS_SAMPLE_URL}, {"url": at_a_tag}, {"url": elsewhere}]},
                "note": note,
            },
        )

        assert prepared == {
            "pages": {"concept": "widgets.CataloguePage", "content": [{"url": UPLOADED_URI}, {"url": UPLOADED_URI}, {"url": elsewhere}]},
            "note": note,
        }
        assert fake_api.calls() == [f"POST {UPLOAD}"]

    def test_a_sample_this_checkout_does_not_hold_stops_the_run_before_it_starts(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        with pytest.raises(CookbookLayoutError, match=f"this checkout holds no file at {SAMPLE_PATH}"):
            run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[1])
        assert fake_api.requests == []

    def test_an_upload_answered_without_a_storage_reference_is_refused(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = _cookbook_with_sample(make_cookbook)
        fake_api.answer("POST", UPLOAD, httpx.Response(200, json={"uri": "https://example.org/catalogue.png", "filename": "catalogue.png"}))
        with pytest.raises(HostedApiError, match="without a pipelex-storage:// reference for catalogue.png"):
            run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[1])
        assert fake_api.calls() == [f"POST {UPLOAD}"]

    @pytest.mark.parametrize(
        ("status_code", "body", "ended"),
        [
            (409, {"title": "Run has no result", "status": 409, "detail": "Run finished with status CANCELLED; there is no result."}, "CANCELLED"),
            (409, {"title": "Run has no result", "status": 409, "detail": "The run could not complete."}, "FAILED"),
            (200, {"pipeline_run_id": RUN_ID, "main_stuff": None}, "COMPLETED"),
        ],
        ids=["cancelled", "failed-without-a-status-word", "completed-without-output"],
    )
    def test_a_run_that_ends_without_a_result_raises_with_its_id_and_status(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, status_code: int, body: dict[str, Any], ended: str
    ):
        cookbook = load_cookbook(make_cookbook())
        fake_api.answer("POST", START, _started())
        fake_api.answer("GET", RESULTS, httpx.Response(status_code, json=body))
        with pytest.raises(HostedRunError) as raised:
            run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0])
        assert (raised.value.run_id, raised.value.status) == (RUN_ID, ended)
        assert not isinstance(raised.value, HostedRunTimeoutError)
        assert str(raised.value).startswith(f"run {RUN_ID} ended {ended} without a result")

    @pytest.mark.parametrize(("retry_after", "waits"), [(None, [5.0, 5.0]), ("900", [600.0, 200.0])], ids=["poll-interval", "retry-after"])
    def test_a_run_still_going_when_the_wait_runs_out_raises_with_its_id(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture, retry_after: str | None, waits: list[float]
    ):
        # Each read of the clock moves it on by 400 seconds, and the wait never sleeps past its deadline.
        ticks = count(start=0, step=400)
        mocker.patch("scripts.hosted.monotonic", side_effect=lambda: float(next(ticks)))
        sleep = mocker.patch("scripts.hosted.sleep")
        cookbook = load_cookbook(make_cookbook())
        fake_api.answer("POST", START, _started())
        fake_api.answer("GET", RESULTS, httpx.Response(202, headers={"Retry-After": retry_after} if retry_after else {}, json={"state": "RUNNING"}))

        with pytest.raises(HostedRunTimeoutError, match=f"run {RUN_ID} was still going after 1000 s") as raised:
            run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0], timeout_seconds=1000)

        assert (raised.value.run_id, raised.value.status) == (RUN_ID, "RUNNING")
        assert [call.args[0] for call in sleep.call_args_list] == waits
        assert fake_api.calls().count(f"GET {RESULTS}") == 3

    def test_a_refused_start_names_the_problem_and_waits_on_nothing(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        problem = {"title": "Pipeline input error", "status": 422, "detail": "The input `text` is missing.", "error_type": "PipelineInputError"}
        fake_api.answer("POST", START, httpx.Response(422, json=problem))
        with pytest.raises(HostedApiError) as raised:
            run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0])
        assert (raised.value.status_code, raised.value.problem["error_type"]) == (422, "PipelineInputError")
        assert fake_api.calls() == [f"POST {START}"]

    def test_a_start_that_gets_no_answer_says_the_run_may_exist(self):
        def time_out(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        client = HostedClient(api_key=FAKE_API_KEY, base_url=FAKE_BASE_URL, transport=httpx.MockTransport(time_out))
        with pytest.raises(HostedApiError, match="may have started the run before the connection failed"):
            client.start_files(mthds_contents=[WORDS_BUNDLE], inputs={"text": "The quick brown fox"})

    def test_the_times_this_process_saw_stand_in_when_the_status_cannot_be_read(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        fake_api.answer("POST", START, _started())
        fake_api.answer("GET", RESULTS, _completed({"text": "four words"}, []))
        fake_api.answer("GET", STATUS, httpx.Response(500, json={"title": "Internal Server Error"}))
        before = datetime.now(UTC)

        run = run_package(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0])

        assert before <= run.started_at <= run.finished_at <= datetime.now(UTC)
        assert run.cost_usd == 0

    def test_storage_references_are_resolved_in_batches_with_refusals_as_values(self, fake_api: FakeApi):
        uris = [f"pipelex-storage://org_1/results/{index}.png" for index in range(150)]
        refusal = {"code": "forbidden", "detail": "The reference belongs to another organization."}

        def verdicts(batch: list[str], *, refused: str | None = None) -> httpx.Response:
            items = [
                {"uri": uri, "url": None, "expires_at": None, "content_type": None, "error": refusal}
                if uri == refused
                else {
                    "uri": uri,
                    "url": f"https://bucket.example.invalid/{uri.removeprefix('pipelex-storage://')}",
                    "expires_at": "2026-09-26T10:15:00Z",
                    "content_type": "image/png",
                }
                for uri in batch
            ]
            return httpx.Response(200, json={"items": items})

        fake_api.answer("POST", RESOLVE, verdicts(uris[:100]), verdicts(uris[100:], refused=uris[-1]))

        resolved = fake_api.client.resolve_storage_urls(uris=uris)

        assert [len(body["uris"]) for body in fake_api.bodies("POST", RESOLVE)] == [100, 50]
        assert [verdict.uri for verdict in resolved] == uris
        assert (resolved[0].url, resolved[0].content_type, resolved[0].error) == (
            "https://bucket.example.invalid/org_1/results/0.png",
            "image/png",
            None,
        )
        assert (resolved[-1].url, resolved[-1].error) == (None, StorageUrlError(**refusal))

    def test_an_answer_that_does_not_follow_the_references_is_refused(self, fake_api: FakeApi):
        uris = ["pipelex-storage://org_1/results/a.png", "pipelex-storage://org_1/results/b.png"]
        fake_api.answer("POST", RESOLVE, httpx.Response(200, json={"items": [{"uri": uris[1]}, {"uri": uris[0]}]}))
        with pytest.raises(HostedApiError, match="one verdict per reference, in the order they were sent"):
            fake_api.client.resolve_storage_urls(uris=uris)
        assert fake_api.client.resolve_storage_urls(uris=[]) == []

    def test_a_storage_link_is_fetched_without_the_key(self):
        requests: list[httpx.Request] = []

        def serve(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, content=b"png bytes")

        assert download(STORAGE_LINK, max_bytes=1024, transport=httpx.MockTransport(serve)) == b"png bytes"
        assert "Authorization" not in requests[0].headers
        assert requests[0].url == httpx.URL(STORAGE_LINK)

    @pytest.mark.parametrize(
        ("url", "answer", "problem"),
        [
            (STORAGE_LINK.replace("https://", "http://"), None, "is not an HTTPS link"),
            (STORAGE_LINK, httpx.Response(403, text="Request has expired"), "answered HTTP 403"),
            (STORAGE_LINK, httpx.Response(302, headers={"Location": "https://elsewhere.example.invalid/"}), "answered HTTP 302"),
            (STORAGE_LINK, httpx.Response(200, content=b"x" * 2048), "holds 2048 bytes, more than the 1024 allowed"),
            (STORAGE_LINK, httpx.Response(200, content=iter([b"x" * 600, b"x" * 600])), "holds more than the 1024 bytes allowed"),
        ],
        ids=["plain-http", "refused", "redirect", "declared-too-long", "streamed-too-long"],
    )
    def test_a_storage_link_that_does_not_give_its_file_within_bounds_is_refused(self, url: str, answer: httpx.Response | None, problem: str):
        def serve(request: httpx.Request) -> httpx.Response:
            assert answer is not None, "a link refused before the fetch is never fetched"
            return answer

        with pytest.raises(HostedApiError) as raised:
            download(url, max_bytes=1024, transport=httpx.MockTransport(serve))
        assert problem in str(raised.value)
        # The link's query holds its signature, which an error never repeats.
        assert "do-not-print" not in str(raised.value)
