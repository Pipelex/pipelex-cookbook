import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image
from pydantic import JsonValue, ValidationError

from scripts.cookbook import MethodPackage, load_cookbook
from scripts.exceptions import CookbookLayoutError
from scripts.snapshot import (
    PREVIEW_LONG_SIDE,
    OutputSnapshot,
    SnapshotRoute,
    bundle_digest,
    document_samples,
    file_name,
    files_digest,
    fit_image,
    inputs_digest,
    is_pdf,
    leftover_links,
    load_snapshot,
    preview_path,
    read_snapshot,
    render_preview,
    rewrite_output,
    sample_files,
    storage_references,
    unrecorded_documents,
    write_previews,
)
from tests.tooling.test_data import (
    WIDGETS_OUTPUT,
    WIDGETS_SAMPLE_PATH,
    MakeCookbook,
    drop_widgets_record,
    make_widgets_sample_a_document,
    make_word_document_sample,
    pdf_bytes,
    png_bytes,
    write_snapshot,
)

RECEIPT_URI = "pipelex-storage://org_1/runs/run_1/outputs/2325fcfe.png"
# In a real SigV4 link's order, where every signing parameter follows an `&`, which HTML writes `&amp;`.
RECEIPT_LINK = (
    "https://bucket.s3.amazonaws.com/org_1/runs/run_1/outputs/2325fcfe.png"
    "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA%2F&X-Amz-Date=20260926T000000Z&X-Amz-Signature=abc123"
)


def _package(root: Path, name: str) -> MethodPackage:
    [package] = [package for package in load_cookbook(root).packages if package.name == name]
    return package


class TestDigests:
    def test_a_digest_hashes_the_sorted_lines_of_path_and_file_hash(self, tmp_path: Path):
        (tmp_path / "b.txt").write_text("bee", encoding="utf-8")
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "c.txt").write_text("sea", encoding="utf-8")
        lines = [
            f"a/c.txt\0{hashlib.sha256(b'sea').hexdigest()}\n",
            f"b.txt\0{hashlib.sha256(b'bee').hexdigest()}\n",
        ]
        expected = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        assert files_digest(root=tmp_path, paths=[tmp_path / "b.txt", tmp_path / "a" / "c.txt"]) == expected

    def test_the_inputs_digest_covers_inputs_json_and_the_local_assets_it_names(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        cookbook = load_cookbook(root)
        package = _package(root, "extract_widgets")
        before = inputs_digest(cookbook=cookbook, package=package)
        (root / WIDGETS_SAMPLE_PATH).write_bytes(png_bytes(width=41, height=30))
        assert inputs_digest(cookbook=cookbook, package=package) != before

    def test_the_inputs_digest_covers_a_local_file_nested_in_a_structured_input(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        url = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/count_words/glossary.png"
        brief = {"title": "The fox", "attachments": [{"label": "Glossary", "image": {"url": url}}]}
        (root / "methods" / "count_words" / "inputs.json").write_text(json.dumps({"text": {"concept": "words.Brief", "content": brief}}))
        glossary = root / "assets" / "count_words" / "glossary.png"
        glossary.parent.mkdir(parents=True)
        glossary.write_bytes(png_bytes(width=10, height=10))
        cookbook = load_cookbook(root)
        package = _package(root, "count_words")
        assert sample_files(cookbook=cookbook, package=package) == [glossary]
        before = inputs_digest(cookbook=cookbook, package=package)
        glossary.write_bytes(png_bytes(width=11, height=10))
        assert inputs_digest(cookbook=cookbook, package=package) != before

    def test_the_bundle_digest_changes_with_a_bundle(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        cookbook = load_cookbook(root)
        package = _package(root, "count_words")
        before = bundle_digest(cookbook=cookbook, package=package)
        bundle = root / "methods" / "count_words" / "bundle.mthds"
        bundle.write_text(bundle.read_text(encoding="utf-8") + "\n# A tweak.\n", encoding="utf-8")
        assert bundle_digest(cookbook=cookbook, package=package) != before

    def test_a_sample_naming_a_file_the_checkout_lacks_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        (root / WIDGETS_SAMPLE_PATH).unlink()
        with pytest.raises(CookbookLayoutError, match="this checkout holds no file at assets/extract_widgets/catalogue.png"):
            inputs_digest(cookbook=load_cookbook(root), package=_package(root, "extract_widgets"))


class TestSnapshotFile:
    def test_a_snapshot_reads_back_as_written_and_omits_resized_unless_it_was(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        written = write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT, files={"output/widgets-0-photo.png": (b"png", "image/png")})
        package = _package(root, "extract_widgets")
        assert read_snapshot(package) == written
        data = json.loads((package.directory / "output.json").read_text(encoding="utf-8"))
        assert data["files"] == {"output/widgets-0-photo.png": {"sha256": hashlib.sha256(b"png").hexdigest(), "content_type": "image/png"}}
        assert data["run"]["started_at"] == "2026-09-28T09:14:02Z"
        assert data["run"]["route"] == "files"
        assert set(data) == {"pipe", "concept", "run", "output", "files"}

    def test_a_package_without_a_snapshot_reads_none(self, make_cookbook: MakeCookbook):
        assert read_snapshot(_package(make_cookbook(with_sample=True), "count_words")) is None

    @pytest.mark.parametrize(
        ("run_update", "message"),
        [
            ({"server": "https://staging.pipelex.com"}, "comes from production"),
            ({"route": "address"}, "an address run names its `method_ref`"),
            ({"method_ref": "github.com/Pipelex/pipelex-cookbook/extract_widgets@v0.9.0"}, "names no `method_ref`"),
            ({"finished_at": "2026-09-28T09:00:00Z"}, "finished before it started"),
            ({"cost_usd": 0.01}, "Extra inputs are not permitted"),
        ],
    )
    def test_a_snapshot_out_of_its_rules_is_refused(self, make_cookbook: MakeCookbook, run_update: dict[str, JsonValue], message: str):
        root = make_cookbook(with_sample=True)
        write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT)
        path = root / "methods" / "extract_widgets" / "output.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["run"].update(run_update)
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match=message):
            load_snapshot(path)

    def test_an_address_run_names_its_address_and_commit(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        written = write_snapshot(root, "extract_widgets", output=WIDGETS_OUTPUT)
        run = written.run.model_copy(
            update={"route": SnapshotRoute.ADDRESS, "method_ref": "github.com/Pipelex/pipelex-cookbook/extract_widgets@v0.9.0", "commit_sha": "abc"}
        )
        snapshot = OutputSnapshot.model_validate({**written.model_dump(mode="json"), "run": run.model_dump(mode="json")})
        assert snapshot.run.route == SnapshotRoute.ADDRESS
        assert snapshot.run.duration_seconds == 37


EXPENSE_OUTPUT: JsonValue = {
    "items": [
        {
            "employee": {"full_name": "Ada"},
            "expenses_with_receipts": [
                {"receipt": {"url": RECEIPT_URI, "public_url": RECEIPT_LINK, "mime_type": "image/png"}},
                {"receipt": {"url": RECEIPT_URI, "public_url": RECEIPT_LINK, "mime_type": "image/png"}},
            ],
            "html_report": {"inner_html": f'<img src="{RECEIPT_LINK.replace("&", "&amp;")}">', "css_class": None},
        }
    ]
}


class TestOutputFiles:
    def test_each_reference_is_found_once_at_its_first_path_with_its_presigned_links(self):
        [reference] = storage_references(EXPENSE_OUTPUT)
        assert reference.uri == RECEIPT_URI
        assert reference.found_at == "$.items[0].expenses_with_receipts[0].receipt.url"
        assert reference.public_urls == [RECEIPT_LINK]

    @pytest.mark.parametrize(
        ("segments", "content_type", "uri", "expected"),
        [
            (["items", 0, "expenses_with_receipts", 2, "receipt", "url"], "image/png", RECEIPT_URI, "items-0-expenses_with_receipts-2-receipt.png"),
            (["url"], "image/jpeg", "pipelex-storage://org/x.jpeg", "output.jpg"),
            ([], None, "pipelex-storage://org/report.pdf", "output.pdf"),
            (["a key", "url"], None, "pipelex-storage://org/blob", "a_key.bin"),
        ],
    )
    def test_a_copied_file_is_named_after_its_first_path(self, segments: list[str | int], content_type: str | None, uri: str, expected: str):
        assert file_name(segments=segments, content_type=content_type, uri=uri) == expected

    def test_rewriting_replaces_every_reference_and_link_and_drops_the_presigned_keys(self):
        local = "output/items-0-expenses_with_receipts-0-receipt.png"
        rewritten = rewrite_output(EXPENSE_OUTPUT, replacements={RECEIPT_URI: local, RECEIPT_LINK: local})
        # Read back as JSON the test walks by hand.
        [item] = cast("Any", rewritten)["items"]
        assert item["expenses_with_receipts"][0]["receipt"] == {"url": local, "mime_type": "image/png"}
        assert item["html_report"]["inner_html"] == f'<img src="{local}">'
        assert leftover_links(rewritten) == []

    def test_a_reference_or_a_signed_link_left_behind_is_found(self):
        leftovers = leftover_links(EXPENSE_OUTPUT)
        assert "$.items[0].expenses_with_receipts[0].receipt.url holds a pipelex-storage:// reference" in leftovers
        assert "$.items[0].expenses_with_receipts[0].receipt.public_url is a presigned link" in leftovers
        assert "$.items[0].html_report.inner_html holds a signed link" in leftovers

    @pytest.mark.parametrize("separator", ["&", "&amp;", "&#38;", "&#x26;", "%26"])
    @pytest.mark.parametrize(
        "query",
        [
            "X-Amz-Algorithm=AWS4-HMAC-SHA256{sep}X-Amz-Credential=AKIA%2F{sep}X-Amz-Signature=abc",
            "AWSAccessKeyId=AKIA{sep}Expires=1{sep}Signature=abc",
            "sv=2024-01-01{sep}se=2026-09-27{sep}sig=abc",
            "X-Goog-Algorithm=GOOG4-RSA-SHA256{sep}X-Goog-Credential=svc{sep}X-Goog-Signature=abc",
            "Expires=1{sep}Signature=abc{sep}Key-Pair-Id=K1",
        ],
    )
    def test_a_signed_link_in_html_is_found_however_its_separators_are_written(self, separator: str, query: str):
        # An input image the runtime renders into HTML carries its presigned link with every `&` escaped, and no storage reference beside it.
        link = "https://files.example.com/org_1/photo.png?" + query.format(sep=separator)
        assert leftover_links({"inner_html": f'<img src="{link}">'}) == ["$.inner_html holds a signed link"]

    def test_an_image_longer_than_the_limit_is_downscaled_in_its_format(self):
        data, resized = fit_image(png_bytes(width=3200, height=1000), content_type="image/png")
        image = Image.open(io.BytesIO(data))
        assert resized is True
        assert image.size == (1600, 500)
        assert image.format == "PNG"

    def test_an_animated_image_is_kept_whole_since_downscaling_would_keep_one_frame(self):
        frames = [Image.new("RGB", (3200, 100), colour) for colour in ("red", "blue")]
        buffer = io.BytesIO()
        frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=100, loop=0)
        animated = buffer.getvalue()
        assert fit_image(animated, content_type="image/gif") == (animated, False)

    def test_a_small_image_and_a_non_image_are_kept_as_they_are(self):
        small = png_bytes(width=1600, height=900)
        assert fit_image(small, content_type="image/png") == (small, False)
        assert fit_image(b"<html></html>", content_type="text/html") == (b"<html></html>", False)


class TestPreviews:
    def test_a_preview_is_the_first_page_rendered_at_its_long_side(self, tmp_path: Path):
        document = tmp_path / "deck.pdf"
        document.write_bytes(pdf_bytes(width=300, height=200))
        image = Image.open(io.BytesIO(render_preview(document)))
        assert image.format == "PNG"
        assert max(image.size) == PREVIEW_LONG_SIDE
        assert preview_path(document) == tmp_path / "deck.preview.png"

    def test_a_file_that_is_not_a_pdf_is_refused(self, tmp_path: Path):
        document = tmp_path / "deck.pdf"
        document.write_bytes(b"not a pdf")
        with pytest.raises(CookbookLayoutError, match="not a PDF that can be previewed"):
            render_preview(document)

    def test_only_document_inputs_kept_here_get_a_preview(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        package = _package(root, "extract_widgets")
        assert document_samples(cookbook=load_cookbook(root), package=package) == []

        (root / WIDGETS_SAMPLE_PATH).write_bytes(pdf_bytes(width=300, height=200))
        make_widgets_sample_a_document(root)
        cookbook = load_cookbook(root)
        package = _package(root, "extract_widgets")
        preview = root / "assets" / "extract_widgets" / "catalogue.preview.png"
        assert document_samples(cookbook=cookbook, package=package) == [root / WIDGETS_SAMPLE_PATH]
        assert write_previews(cookbook=cookbook, package=package) == [preview]
        assert preview.is_file()
        # A preview already holding what the rendering gives is left as it is.
        assert write_previews(cookbook=cookbook, package=package) == []

    @pytest.mark.parametrize(
        ("name", "data", "expected"),
        [
            ("deck.pdf", b"anything", True),
            ("deck.bin", b"%PDF-1.7 and the rest", True),
            ("letter.docx", b"PK\x03\x04 a Word document", False),
            ("scan.png", png_bytes(width=4, height=4), False),
        ],
    )
    def test_a_pdf_is_known_by_its_extension_or_its_header(self, tmp_path: Path, name: str, data: bytes, expected: bool):
        path = tmp_path / name
        path.write_bytes(data)
        assert is_pdf(path) is expected

    def test_a_document_sample_that_is_no_pdf_gets_no_preview(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        make_word_document_sample(root)
        cookbook = load_cookbook(root)
        package = _package(root, "extract_widgets")
        assert document_samples(cookbook=cookbook, package=package) == []
        assert write_previews(cookbook=cookbook, package=package) == []
        assert not (root / "assets" / "extract_widgets" / "catalogue.preview.png").exists()
        # Nor is it named as waiting for its record to get one.
        drop_widgets_record(root)
        assert unrecorded_documents(cookbook=load_cookbook(root), package=_package(root, "extract_widgets")) == []

    def test_a_document_sample_without_its_record_never_gets_a_preview(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        (root / WIDGETS_SAMPLE_PATH).write_bytes(pdf_bytes(width=300, height=200))
        make_widgets_sample_a_document(root)
        drop_widgets_record(root)
        cookbook = load_cookbook(root)
        package = _package(root, "extract_widgets")
        assert document_samples(cookbook=cookbook, package=package) == []
        assert unrecorded_documents(cookbook=cookbook, package=package) == [root / WIDGETS_SAMPLE_PATH]
        assert write_previews(cookbook=cookbook, package=package) == []
        assert not (root / "assets" / "extract_widgets" / "catalogue.preview.png").exists()


def test_snapshot_rejects_an_unknown_field():
    with pytest.raises(ValidationError):
        OutputSnapshot.model_validate({"pipe": "p", "concept": "c", "run": {}, "output": None, "files": {}, "cost_usd": 1})
