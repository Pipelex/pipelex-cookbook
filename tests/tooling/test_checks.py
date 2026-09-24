from pathlib import Path

import httpx
import pytest

from scripts import checks
from scripts.checks import check_links, collect_urls, http_status, lockstep_problems, stale_pages
from scripts.cookbook import load_cookbook
from scripts.render import render_pages
from tests.tooling.test_data import WIDGETS_SAMPLE_URL, MakeCookbook


class TestChecks:
    def test_committed_pages_equal_to_a_fresh_render_are_fresh(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_pages(cookbook=cookbook, templates_dir=templates_dir)
        for page_path, contents in rendered.items():
            page_path.write_text(contents, encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=rendered) == []

    def test_a_hand_edit_makes_a_page_stale(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_pages(cookbook=cookbook, templates_dir=templates_dir)
        for page_path, contents in rendered.items():
            page_path.write_text(contents, encoding="utf-8")
        edited = cookbook.root / "methods" / "count_words" / "README.md"
        edited.write_text(edited.read_text(encoding="utf-8").replace("# Word Count", "# Word Counter"), encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=rendered) == [Path("methods/count_words/README.md")]

    def test_a_page_never_written_is_stale(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_pages(cookbook=cookbook, templates_dir=templates_dir)
        assert sorted(stale_pages(cookbook=cookbook, rendered=rendered)) == [
            Path("methods/count_words/README.md"),
            Path("methods/extract_widgets/README.md"),
        ]

    def test_manifests_in_lockstep_pass(self, make_cookbook: MakeCookbook):
        assert lockstep_problems(load_cookbook(make_cookbook())) == []

    def test_a_stray_manifest_version_fails_lockstep(self, make_cookbook: MakeCookbook):
        problems = lockstep_problems(load_cookbook(make_cookbook(widgets_version="0.8.0")))
        assert problems == ["methods/extract_widgets/METHODS.toml declares version 0.8.0, but the cookbook is at 0.9.0"]

    def test_links_into_the_cookbook_need_a_local_file_and_other_links_need_an_answer(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_pages(cookbook=cookbook, templates_dir=templates_dir)

        def not_found(url: str) -> int:
            return 404

        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=cookbook, rendered=rendered, fetch_status=not_found)}
        # The widgets sample is not in this checkout, so it is broken whatever the remote says.
        assert verdicts[WIDGETS_SAMPLE_URL].ok is False
        assert verdicts[WIDGETS_SAMPLE_URL].found_in == ["methods/extract_widgets/README.md", "methods/extract_widgets/inputs.json"]
        # The inputs file is here, so an unanswered URL at the page's tag is only not published yet.
        inputs_url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.9.0/methods/count_words/inputs.json"
        assert verdicts[inputs_url].ok is True
        assert verdicts[inputs_url].note.startswith("not published at v0.9.0")

        sample_path = cookbook.root / "assets" / "extract_widgets" / "catalogue.png"
        sample_path.parent.mkdir(parents=True)
        sample_path.write_bytes(b"png")
        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=cookbook, rendered=rendered, fetch_status=not_found)}
        assert verdicts[WIDGETS_SAMPLE_URL].ok is True

    def test_a_link_into_the_cookbook_names_its_local_file_percent_decoded(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/extract_widgets/spring%20catalogue.png"
        (root / "methods" / "extract_widgets" / "inputs.json").write_text(f'{{"catalogue": {{"url": "{url}"}}}}', encoding="utf-8")
        sample_path = root / "assets" / "extract_widgets" / "spring catalogue.png"
        sample_path.parent.mkdir(parents=True)
        sample_path.write_bytes(b"png")

        def not_found(url: str) -> int:
            return 404

        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=load_cookbook(root), rendered={}, fetch_status=not_found)}
        assert verdicts[url].ok is True

    def test_a_sample_hosted_elsewhere_must_answer(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        url = "https://example.com/datasets/report.pdf"
        (root / "methods" / "extract_widgets" / "inputs.json").write_text(f'{{"catalogue": [{{"url": "{url}"}}]}}', encoding="utf-8")
        cookbook = load_cookbook(root)

        def not_found(url: str) -> int:
            return 404

        def found(url: str) -> int:
            return 200

        assert {verdict.url: verdict.ok for verdict in check_links(cookbook=cookbook, rendered={}, fetch_status=not_found)} == {url: False}
        assert {verdict.url: verdict.ok for verdict in check_links(cookbook=cookbook, rendered={}, fetch_status=found)} == {url: True}

    def test_a_url_closing_a_sentence_on_a_page_drops_the_full_stop(self, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/extract_widgets/catalogue.png"
        page = cookbook.root / "methods" / "extract_widgets" / "README.md"
        found = collect_urls(cookbook=cookbook, rendered={page: f"Run it on {url}."})
        assert url in found
        assert f"{url}." not in found

    def test_a_link_into_the_cookbook_that_fails_otherwise_than_404_is_broken(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_pages(cookbook=cookbook, templates_dir=templates_dir)
        inputs_url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.9.0/methods/count_words/inputs.json"

        def server_error(url: str) -> int:
            return 500

        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=cookbook, rendered=rendered, fetch_status=server_error)}
        assert verdicts[inputs_url].ok is False


def _served_by(monkeypatch: pytest.MonkeyPatch, answer: dict[str, int]) -> list[str]:
    """Serve every request from `answer`, a status per method, and return the methods asked, in order."""
    methods: list[str] = []
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        return httpx.Response(answer[request.method])

    def serving_client(*, follow_redirects: bool, timeout: float) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler), follow_redirects=follow_redirects, timeout=timeout)

    monkeypatch.setattr(checks.httpx, "Client", serving_client)
    return methods


class TestHttpStatus:
    def test_a_url_answering_head_is_not_fetched(self, monkeypatch: pytest.MonkeyPatch):
        methods = _served_by(monkeypatch, {"HEAD": 200, "GET": 500})
        assert http_status("https://example.com/report.pdf") == 200
        assert methods == ["HEAD"]

    @pytest.mark.parametrize("head_status", [403, 404, 405, 501])
    def test_a_host_refusing_head_is_asked_with_get(self, monkeypatch: pytest.MonkeyPatch, head_status: int):
        methods = _served_by(monkeypatch, {"HEAD": head_status, "GET": 200})
        assert http_status("https://example.com/report.pdf") == 200
        assert methods == ["HEAD", "GET"]

    def test_a_url_missing_for_get_too_is_missing(self, monkeypatch: pytest.MonkeyPatch):
        _served_by(monkeypatch, {"HEAD": 404, "GET": 404})
        assert http_status("https://example.com/report.pdf") == 404
