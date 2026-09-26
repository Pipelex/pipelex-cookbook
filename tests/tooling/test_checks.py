from pathlib import Path

import httpx
import pytest
from pydantic import JsonValue

from scripts import checks
from scripts.checks import (
    check_links,
    collect_urls,
    http_status,
    lockstep_problems,
    orphan_snippet_dirs,
    sample_problems,
    snapshot_problems,
    stale_pages,
    stale_snapshots,
)
from scripts.cookbook import load_cookbook
from scripts.render import render_all, render_pages
from tests.tooling.test_data import (
    WIDGETS_OUTPUT,
    WIDGETS_SAMPLE_URL,
    MakeCookbook,
    drop_widgets_record,
    make_widgets_sample_a_document,
    make_widgets_sample_synthetic,
    png_bytes,
    write_snapshot,
)


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

    def test_a_hand_edit_makes_a_snippet_file_stale(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_all(cookbook=cookbook, templates_dir=templates_dir)
        for path, contents in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=rendered) == []
        edited = cookbook.root / "tests" / "snippets" / "count_words" / "python" / "snippet.py"
        edited.write_text(edited.read_text(encoding="utf-8").replace("print(result.main_stuff)", "print(result)"), encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=rendered) == [Path("tests/snippets/count_words/python/snippet.py")]

    def test_a_snippet_directory_of_no_method_is_an_orphan(self, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        snippets_root = cookbook.root / "tests" / "snippets"
        for directory in ("count_words", "extract_widgets", "retired_method", "node_modules"):
            (snippets_root / directory).mkdir(parents=True)
        (snippets_root / "package.json").write_text("{}", encoding="utf-8")
        assert orphan_snippet_dirs(cookbook) == [Path("tests/snippets/retired_method")]

    def test_a_cookbook_without_snippets_has_no_orphan(self, make_cookbook: MakeCookbook):
        assert orphan_snippet_dirs(load_cookbook(make_cookbook())) == []

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

    def test_a_link_into_the_cookbook_climbing_out_of_the_checkout_is_broken(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        (root.parent / "outside.txt").write_text("not the cookbook's", encoding="utf-8")
        url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/../outside.txt"
        (root / "methods" / "extract_widgets" / "inputs.json").write_text(f'{{"catalogue": {{"url": "{url}"}}}}', encoding="utf-8")
        # Loading refuses a real sample linked outside its own `assets/<name>/`, so the link check meets this one as a made-up sample.
        make_widgets_sample_synthetic(root)

        def found(url: str) -> int:
            return 200

        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=load_cookbook(root), rendered={}, fetch_status=found)}
        assert (verdicts[url].ok, verdicts[url].note) == (False, "its path ../outside.txt leads outside this checkout")

    def test_a_sample_hosted_elsewhere_must_answer(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        url = "https://example.com/datasets/report.pdf"
        (root / "methods" / "extract_widgets" / "inputs.json").write_text(f'{{"catalogue": [{{"url": "{url}"}}]}}', encoding="utf-8")
        # A real sample is copied into this repository, so a sample hosted elsewhere is one made up for the example.
        make_widgets_sample_synthetic(root)
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

    def test_raw_urls_in_the_recipes_files_are_collected_whatever_the_file(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        sample = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/extract_gantt/gantt_tree_house.png"
        invoice = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/assets/invoice_extractor/invoice_1.pdf"
        vendored = "https://raw.githubusercontent.com/some/package/main/logo.png"
        http_recipe = root / "recipes" / "run" / "http"
        http_recipe.mkdir(parents=True)
        (http_recipe / "README.md").write_text(f"sh run.sh {sample}\n", encoding="utf-8")
        (http_recipe / "run.sh").write_text(f'SAMPLE="{sample}"\n', encoding="utf-8")
        (http_recipe / "chart.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
        csv_recipe = root / "recipes" / "code" / "python" / "csv-batch"
        csv_recipe.mkdir(parents=True)
        (csv_recipe / "invoices.csv").write_text(f"invoice_url\n{invoice}\n", encoding="utf-8")
        (csv_recipe / "node_modules" / "some-package").mkdir(parents=True)
        (csv_recipe / "node_modules" / "some-package" / "README.md").write_text(vendored, encoding="utf-8")
        (csv_recipe / "generated" / "invoice_extraction").mkdir(parents=True)
        (csv_recipe / "generated" / "invoice_extraction" / "models.py").write_text(f'"""{vendored}"""\n', encoding="utf-8")
        found = collect_urls(cookbook=load_cookbook(root), rendered={})
        assert found[sample] == ["recipes/run/http/README.md", "recipes/run/http/run.sh"]
        assert found[invoice] == ["recipes/code/python/csv-batch/invoices.csv"]
        assert vendored not in found

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


class TestSampleAndSnapshotChecks:
    def test_an_input_without_its_record_is_a_problem(self, make_cookbook: MakeCookbook):
        assert sample_problems(load_cookbook(make_cookbook(with_sample=True))) == [
            "methods/count_words: the sample input `text` has no source-and-licence record under [methods.count_words.samples.text] in cookbook.toml"
        ]

    def test_a_document_sample_kept_here_needs_its_preview(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        make_widgets_sample_a_document(root)
        problems = sample_problems(load_cookbook(root))
        assert (
            "methods/extract_widgets: the document sample assets/extract_widgets/catalogue.png has no preview, "
            "assets/extract_widgets/catalogue.preview.png; `make previews` renders it, with no key and no run"
        ) in problems
        (root / "assets" / "extract_widgets" / "catalogue.preview.png").write_bytes(b"png")
        assert len(sample_problems(load_cookbook(root))) == 1

    def test_a_document_sample_without_its_record_is_reported_for_the_record_alone(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        make_widgets_sample_a_document(root)
        drop_widgets_record(root)
        problems = sample_problems(load_cookbook(root))
        assert (
            "methods/extract_widgets: the sample input `catalogue` has no source-and-licence record "
            "under [methods.extract_widgets.samples.catalogue] in cookbook.toml"
        ) in problems
        assert not [problem for problem in problems if "preview" in problem]

    def test_a_method_without_a_snapshot_is_a_problem(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT)
        assert snapshot_problems(load_cookbook(root)) == [
            "methods/count_words has no output.json: `make snapshot METHOD=count_words` takes it, with one paid run on production"
        ]

    def test_a_snapshot_taken_from_the_package_as_it_is_holds(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        write_snapshot(root, "count_words", output={"text": "Four words."})
        write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT, files={"output/photo.png": (png_bytes(width=4, height=4), "image/png")})
        cookbook = load_cookbook(root)
        assert snapshot_problems(cookbook) == []
        assert stale_snapshots(cookbook) == []

    def test_a_snapshot_of_another_pipe_or_concept_is_a_problem(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT)
        path = root / "methods" / "extract_widgets" / "output.json"
        path.write_text(path.read_text(encoding="utf-8").replace('"widgets.WidgetList"', '"widgets.Widget"'), encoding="utf-8")
        problems = [problem for problem in snapshot_problems(load_cookbook(root)) if problem.startswith("methods/extract_widgets")]
        assert problems == [
            "methods/extract_widgets/output.json holds a `widgets.Widget`, and contract.json says the method returns a `widgets.WidgetList`"
        ]

    def test_a_snapshot_of_another_sample_is_a_problem_and_of_other_bundles_only_stale(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT)
        bundle = root / "methods" / "extract_widgets" / "bundle.mthds"
        bundle.write_text(bundle.read_text(encoding="utf-8") + "\n# A prompt tweak.\n", encoding="utf-8")
        cookbook = load_cookbook(root)
        assert [problem for problem in snapshot_problems(cookbook) if problem.startswith("methods/extract_widgets")] == []
        assert stale_snapshots(cookbook) == [
            "methods/extract_widgets/output.json was taken from other bundles than the package's: "
            "whoever changes what the method returns takes a new one with `make snapshot METHOD=extract_widgets`"
        ]

        (root / "assets" / "extract_widgets" / "catalogue.png").write_bytes(png_bytes(width=41, height=30))
        problems = [problem for problem in snapshot_problems(load_cookbook(root)) if problem.startswith("methods/extract_widgets")]
        assert problems == [
            "methods/extract_widgets/output.json was taken from another sample than inputs.json and the assets it names: "
            "the page would show one input beside another's output"
        ]

    def test_the_snapshots_files_must_be_those_it_names(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        output: JsonValue = {"widgets": [{"name": "Sprocket", "photo": {"url": "output/widgets-0-photo.png"}}]}
        files = {"output/widgets-0-photo.png": (png_bytes(width=4, height=4), "image/png"), "output/extra.png": (b"x", "image/png")}
        write_snapshot(root, "extract_widgets", output=output, files=files)
        package_dir = root / "methods" / "extract_widgets"
        assert [problem for problem in snapshot_problems(load_cookbook(root)) if problem.startswith("methods/extract_widgets")] == []

        (package_dir / "output" / "widgets-0-photo.png").write_bytes(b"edited")
        (package_dir / "output" / "extra.png").unlink()
        (package_dir / "output" / "stray.png").write_bytes(b"stray")
        path = package_dir / "output.json"
        path.write_text(
            path.read_text(encoding="utf-8").replace('"url": "output/widgets-0-photo.png"', '"url": "output/unlisted.png"'), encoding="utf-8"
        )
        problems = [problem for problem in snapshot_problems(load_cookbook(root)) if problem.startswith("methods/extract_widgets")]
        assert problems == [
            "methods/extract_widgets/output.json names the file output/widgets-0-photo.png, whose contents changed since the snapshot",
            "methods/extract_widgets/output.json names the file output/extra.png, which does not exist",
            "methods/extract_widgets/output.json holds the path output/unlisted.png, which its `files` does not list",
            "methods/extract_widgets/output.json does not name output/stray.png, which output/ holds: `make snapshot` replaces output/ as a whole",
        ]

    def test_a_snapshot_that_does_not_load_is_a_problem(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        (root / "methods" / "count_words" / "output.json").write_text("{not json", encoding="utf-8")
        [problem, _] = snapshot_problems(load_cookbook(root))
        assert "not an output snapshot; take it again with `make snapshot METHOD=count_words`" in problem
