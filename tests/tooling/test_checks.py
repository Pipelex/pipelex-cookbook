from pathlib import Path

from scripts.checks import check_links, lockstep_problems, stale_pages
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
        assert verdicts[inputs_url].note.startswith("not published at v0.9.0 yet")

        sample_path = cookbook.root / "assets" / "extract_widgets" / "catalogue.png"
        sample_path.parent.mkdir(parents=True)
        sample_path.write_bytes(b"png")
        verdicts = {verdict.url: verdict for verdict in check_links(cookbook=cookbook, rendered=rendered, fetch_status=not_found)}
        assert verdicts[WIDGETS_SAMPLE_URL].ok is True
