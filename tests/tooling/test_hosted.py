import httpx
import pytest

from scripts.exceptions import HostedApiError
from scripts.hosted import HostedClient


class TestHosted:
    def test_a_200_whose_body_is_not_json_is_a_hosted_api_error(self, monkeypatch: pytest.MonkeyPatch):
        def fake_post(url: str, **_: object) -> httpx.Response:
            return httpx.Response(200, text="<html>maintenance</html>", request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", fake_post)
        client = HostedClient(api_key="not-a-real-key", base_url="https://api.example.invalid")
        with pytest.raises(HostedApiError, match="not JSON"):
            client.validate_files(contents=["domain = 'x'"], sources=["x.mthds"])
