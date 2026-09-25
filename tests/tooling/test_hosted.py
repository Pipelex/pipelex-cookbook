import httpx
import pytest

from scripts.cookbook import load_cookbook
from scripts.exceptions import HostedApiError
from scripts.hosted import AddressState, HostedClient, check_address, check_method_ref
from tests.tooling.test_data import MakeCookbook

# The problem details production answered on 2026-09-25, cut down to what the address check reads.
PACKAGE_NOT_FOUND: dict[str, object] = {
    "type": "https://docs.pipelex.com/latest/errors/method-package-not-found-error/",
    "title": "Method package not found",
    "status": 404,
    "detail": "No package at address 'github.com/Pipelex/pipelex-cookbook/count_words' in the fetched repository.",
    "error_type": "MethodPackageNotFoundError",
}
NO_SUCH_TAG: dict[str, object] = {
    "type": "https://docs.pipelex.com/latest/errors/method-fetch-error/",
    "title": "Method fetch",
    "status": 422,
    "detail": "'v0.9.0' in method reference 'github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0' does not name a git tag on the repository.",
    "error_type": "MethodFetchError",
}
REPOSITORY_UNREACHABLE: dict[str, object] = {
    "type": "https://docs.pipelex.com/latest/errors/method-fetch-error/",
    "title": "Method fetch",
    "status": 422,
    "detail": "The repository could not be cloned.",
    "error_type": "MethodFetchError",
}


def _answering(monkeypatch: pytest.MonkeyPatch, *, status: int, body: dict[str, object]) -> list[dict[str, object]]:
    """Make every POST answer `status` with `body`, and return the list the request bodies are appended to."""
    requests: list[dict[str, object]] = []

    def fake_post(url: str, *, json: dict[str, object], **_: object) -> httpx.Response:
        requests.append(json)
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    return requests


def _client() -> HostedClient:
    return HostedClient(api_key="not-a-real-key", base_url="https://api.example.invalid")


class TestHosted:
    def test_a_200_whose_body_is_not_json_is_a_hosted_api_error(self, monkeypatch: pytest.MonkeyPatch):
        def fake_post(url: str, **_: object) -> httpx.Response:
            return httpx.Response(200, text="<html>maintenance</html>", request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", fake_post)
        with pytest.raises(HostedApiError, match="not JSON"):
            _client().validate_files(contents=["domain = 'x'"], sources=["x.mthds"])

    def test_a_refusal_carries_its_status_and_problem_details(self, monkeypatch: pytest.MonkeyPatch):
        _answering(monkeypatch, status=404, body=PACKAGE_NOT_FOUND)
        with pytest.raises(HostedApiError) as raised:
            _client().validate_address(method_ref="github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0")
        assert raised.value.status_code == 404
        assert raised.value.problem["error_type"] == "MethodPackageNotFoundError"

    def test_an_address_is_validated_at_the_page_tag(self, monkeypatch: pytest.MonkeyPatch, make_cookbook: MakeCookbook):
        requests = _answering(monkeypatch, status=200, body={"is_valid": True, "message": "MTHDS content validated successfully"})
        cookbook = load_cookbook(make_cookbook())
        verdict = check_address(client=_client(), cookbook=cookbook, package=cookbook.packages[0])
        assert verdict.state is AddressState.VALID
        assert requests[0]["method_ref"] == "github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0"

    def test_a_recipe_address_is_validated_as_pinned_and_named_after_its_recipe(self, monkeypatch: pytest.MonkeyPatch):
        requests = _answering(monkeypatch, status=200, body={"is_valid": True, "message": "MTHDS content validated successfully"})
        address = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
        verdict = check_method_ref(client=_client(), name="recipes/code/python/csv-batch", address=address)
        assert (verdict.name, verdict.address, verdict.state) == ("recipes/code/python/csv-batch", address, AddressState.VALID)
        assert requests[0]["method_ref"] == address

    @pytest.mark.parametrize(
        ("status", "body", "expected"),
        [
            (404, PACKAGE_NOT_FOUND, AddressState.UNRELEASED),
            (422, NO_SUCH_TAG, AddressState.UNRELEASED),
            (422, REPOSITORY_UNREACHABLE, AddressState.FAILED),
            (500, {"title": "Internal Server Error"}, AddressState.FAILED),
            (200, {"is_valid": False, "message": "The bundle does not parse"}, AddressState.FAILED),
        ],
        ids=["package-not-at-the-tag", "tag-not-pushed", "other-fetch-error", "server-error", "invalid-verdict"],
    )
    def test_only_a_method_missing_at_its_tag_is_unreleased(
        self, monkeypatch: pytest.MonkeyPatch, make_cookbook: MakeCookbook, status: int, body: dict[str, object], expected: AddressState
    ):
        _answering(monkeypatch, status=status, body=body)
        cookbook = load_cookbook(make_cookbook())
        assert check_address(client=_client(), cookbook=cookbook, package=cookbook.packages[0]).state is expected
