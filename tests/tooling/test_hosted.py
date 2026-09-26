from pathlib import Path

import httpx
import pytest

from scripts.cookbook import load_cookbook
from scripts.exceptions import HostedApiError
from scripts.hosted import AddressState, check_address, check_method_ref, check_pinned_method_ref, validate_bundle_file
from tests.tooling.fake_api import FAKE_API_KEY, FakeApi
from tests.tooling.test_data import MakeCookbook

VALIDATE = "/v1/validate"
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
VALID: dict[str, object] = {"is_valid": True, "message": "MTHDS content validated successfully"}


class TestHosted:
    def test_a_200_whose_body_is_not_json_is_a_hosted_api_error(self, fake_api: FakeApi):
        fake_api.answer("POST", VALIDATE, httpx.Response(200, text="<html>maintenance</html>"))
        with pytest.raises(HostedApiError, match="not JSON"):
            fake_api.client.validate_files(contents=["domain = 'x'"], sources=["x.mthds"])

    def test_a_refusal_carries_its_status_and_problem_details(self, fake_api: FakeApi):
        fake_api.answer("POST", VALIDATE, httpx.Response(404, json=PACKAGE_NOT_FOUND))
        with pytest.raises(HostedApiError) as raised:
            fake_api.client.validate_address(method_ref="github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0")
        assert raised.value.status_code == 404
        assert raised.value.problem["error_type"] == "MethodPackageNotFoundError"

    def test_the_key_is_sent_as_the_bearer_token(self, fake_api: FakeApi):
        fake_api.answer("POST", VALIDATE, httpx.Response(200, json=VALID))
        fake_api.client.validate_address(method_ref="github.com/Pipelex/methods/invoice_extraction@v0.1.1")
        assert fake_api.requests[0].headers["Authorization"] == f"Bearer {FAKE_API_KEY}"

    def test_an_address_is_validated_at_the_page_tag(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        fake_api.answer("POST", VALIDATE, httpx.Response(200, json=VALID))
        cookbook = load_cookbook(make_cookbook())
        verdict = check_address(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0])
        assert verdict.state is AddressState.VALID
        assert fake_api.bodies("POST", VALIDATE)[0]["method_ref"] == "github.com/Pipelex/pipelex-cookbook/count_words@v0.9.0"

    def test_a_recipe_address_is_validated_as_pinned_and_named_after_its_recipe(self, fake_api: FakeApi):
        fake_api.answer("POST", VALIDATE, httpx.Response(200, json=VALID))
        address = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
        verdict = check_method_ref(client=fake_api.client, name="recipes/code/python/csv-batch", address=address)
        assert (verdict.name, verdict.address, verdict.state) == ("recipes/code/python/csv-batch", address, AddressState.VALID)
        assert fake_api.bodies("POST", VALIDATE)[0]["method_ref"] == address

    @pytest.mark.parametrize(("status", "body"), [(404, PACKAGE_NOT_FOUND), (422, NO_SUCH_TAG)], ids=["package-not-at-the-tag", "no-such-tag"])
    def test_a_recipe_address_that_does_not_resolve_fails_rather_than_waiting_for_a_release(
        self, fake_api: FakeApi, status: int, body: dict[str, object]
    ):
        fake_api.answer("POST", VALIDATE, httpx.Response(status, json=body))
        address = "github.com/Pipelex/methods/invoice_extraction@v0.1.99"
        verdict = check_pinned_method_ref(client=fake_api.client, name="recipes/code/python/csv-batch", address=address)
        assert verdict.state is AddressState.FAILED
        assert verdict.report == body["detail"]

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
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, status: int, body: dict[str, object], expected: AddressState
    ):
        fake_api.answer("POST", VALIDATE, httpx.Response(status, json=body))
        cookbook = load_cookbook(make_cookbook())
        assert check_address(client=fake_api.client, cookbook=cookbook, package=cookbook.packages[0]).state is expected

    @pytest.mark.parametrize(
        ("body", "is_valid", "report"),
        [
            (VALID, True, "MTHDS content validated successfully"),
            ({"is_valid": False, "rendered_markdown": "Pipe `hello` names no output"}, False, "Pipe `hello` names no output"),
        ],
        ids=["valid", "invalid"],
    )
    def test_a_bundle_is_validated_alone_under_its_path_from_the_root(
        self, fake_api: FakeApi, tmp_path: Path, body: dict[str, object], is_valid: bool, report: str
    ):
        fake_api.answer("POST", VALIDATE, httpx.Response(200, json=body))
        bundle = tmp_path / "tutorial" / "easy" / "hello.mthds"
        bundle.parent.mkdir(parents=True)
        bundle.write_text('domain = "hello"\n', encoding="utf-8")

        verdict = validate_bundle_file(client=fake_api.client, path=bundle, root=tmp_path)

        assert (verdict.source, verdict.is_valid, verdict.report) == ("tutorial/easy/hello.mthds", is_valid, report)
        [request_body] = fake_api.bodies("POST", VALIDATE)
        assert request_body["mthds_contents"] == ['domain = "hello"\n']
        assert request_body["mthds_sources"] == ["tutorial/easy/hello.mthds"]
