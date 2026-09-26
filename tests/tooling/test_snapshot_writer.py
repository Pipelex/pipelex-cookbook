"""The snapshot writer, run against a stand-in for production: no test reaches the network or spends credit."""

import io
import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest
from PIL import Image
from pydantic import JsonValue
from pytest_mock import MockerFixture

from scripts.checks import snapshot_problems
from scripts.contract import ContractOutput
from scripts.cookbook import Cookbook, MethodPackage, load_cookbook
from scripts.exceptions import HostedApiError, SnapshotError
from scripts.hosted import HostedClient, MethodVerdict, download
from scripts.snapshot import PRODUCTION_URL, bundle_digest, inputs_digest, load_snapshot, take_snapshot
from tests.tooling.fake_api import FAKE_API_KEY, FakeApi
from tests.tooling.test_data import (
    WIDGETS_CONTRACT,
    WIDGETS_SAMPLE_PATH,
    MakeCookbook,
    drop_widgets_record,
    make_widgets_sample_a_document,
    png_bytes,
    write_snapshot,
)

START = "/v1/start"
UPLOAD = "/v1/upload"
RESOLVE = "/v1/resolve-storage-url/bulk"
RUN_ID = "run_0456"
RESULTS = f"/v1/runs/{RUN_ID}/results"
STATUS = f"/v1/runs/{RUN_ID}/status"
PHOTO_URI = "pipelex-storage://org_1/runs/run_0456/outputs/9a1b.png"
PHOTO_PUBLIC_URL = "https://bucket.example.invalid/org_1/runs/run_0456/outputs/9a1b.png?X-Amz-Credential=AKIA&X-Amz-Signature=old"
PHOTO_FRESH_URL = "https://bucket.example.invalid/org_1/runs/run_0456/outputs/9a1b.png?X-Amz-Signature=fresh"
SHEET_URI = "pipelex-storage://org_1/runs/run_0456/outputs/7c2d.png"
SHEET_FRESH_URL = "https://bucket.example.invalid/org_1/runs/run_0456/outputs/7c2d.png?X-Amz-Signature=fresh"
# What every error raised once the run completed says of it: how to read its paid output again.
READ_AGAIN = f"The output is paid for: GET /v1/runs/{RUN_ID}/results reads it again"
# The snapshot the package held before the run, whose file is under `output/`.
EARLIER_PHOTO = "output/widgets-0-photo.png"
STATUS_BODY: dict[str, Any] = {
    "pipeline_run_id": RUN_ID,
    "status": "COMPLETED",
    "created_at": "2026-09-28T09:14:02.512Z",
    "finished_at": "2026-09-28T11:14:39+02:00",
}
USAGES: list[dict[str, Any]] = [{"model_type": "llm", "cost": 0.0125}]


def _production_client(fake_api: FakeApi) -> HostedClient:
    return HostedClient(api_key=FAKE_API_KEY, base_url=PRODUCTION_URL, transport=fake_api.transport)


def _widgets(make_cookbook: MakeCookbook) -> tuple[Cookbook, MethodPackage]:
    cookbook = load_cookbook(make_cookbook(with_sample=True))
    return cookbook, cookbook.packages[1]


def _validates(mocker: MockerFixture, package: MethodPackage, *, is_valid: bool = True) -> None:
    verdict = MethodVerdict(name=package.name, is_valid=is_valid, report="verdict report", contract=package.contract if is_valid else None)
    mocker.patch("scripts.snapshot.validate_package", return_value=verdict)


def _runs_to(fake_api: FakeApi, main_stuff: Any) -> None:
    fake_api.answer("POST", UPLOAD, httpx.Response(200, json={"uri": "pipelex-storage://org_1/assets/c.png", "filename": "catalogue.png"}))
    fake_api.answer("POST", START, httpx.Response(202, json={"pipeline_run_id": RUN_ID, "state": "STARTED"}))
    fake_api.answer("GET", RESULTS, httpx.Response(200, json={"pipeline_run_id": RUN_ID, "main_stuff": main_stuff, "tokens_usages": USAGES}))
    fake_api.answer("GET", STATUS, httpx.Response(200, json=STATUS_BODY))


def _widgets_returning_a_list(make_cookbook: MakeCookbook) -> tuple[Cookbook, MethodPackage]:
    """The fixture cookbook, its widget extraction declaring a list of widgets in its bundle and its contract."""
    root = make_cookbook(with_sample=True)
    package_dir = root / "methods" / "extract_widgets"
    bundle = package_dir / "bundle.mthds"
    bundle.write_text(bundle.read_text(encoding="utf-8").replace('output = "WidgetList"', 'output = "Widget[]"'), encoding="utf-8")
    contract = WIDGETS_CONTRACT.model_copy(update={"output": ContractOutput(concept="widgets.Widget", multiplicity="variable")})
    (package_dir / "contract.json").write_text(contract.to_json(), encoding="utf-8")
    cookbook = load_cookbook(root)
    return cookbook, cookbook.packages[1]


def _two_photos_output() -> dict[str, Any]:
    return {
        "widgets": [
            {"name": "Sprocket", "photo": {"url": PHOTO_URI, "mime_type": "image/png"}},
            {"name": "Flange", "photo": {"url": SHEET_URI, "mime_type": "image/png"}},
        ]
    }


def _resolves_both(fake_api: FakeApi) -> None:
    items = [
        {"uri": PHOTO_URI, "url": PHOTO_FRESH_URL, "content_type": "image/png"},
        {"uri": SHEET_URI, "url": SHEET_FRESH_URL, "content_type": "image/png"},
    ]
    fake_api.answer("POST", RESOLVE, httpx.Response(200, json={"items": items}))


def _write_earlier_snapshot(cookbook: Cookbook) -> tuple[str, bytes]:
    """Write the snapshot the package held before the run, and return its `output.json` and the bytes of its one file."""
    photo = png_bytes(width=5, height=5, colour="green")
    output: JsonValue = {"widgets": [{"name": "Gear", "photo": {"url": EARLIER_PHOTO, "mime_type": "image/png"}}]}
    write_snapshot(cookbook.root, "extract_widgets", output=output, files={EARLIER_PHOTO: (photo, "image/png")})
    return (cookbook.root / "methods" / "extract_widgets" / "output.json").read_text(encoding="utf-8"), photo


def _assert_earlier_snapshot_whole(package: MethodPackage, *, snapshot_json: str, photo: bytes) -> None:
    assert (package.directory / "output.json").read_text(encoding="utf-8") == snapshot_json
    assert sorted(path.name for path in (package.directory / "output").iterdir()) == ["widgets-0-photo.png"]
    assert (package.directory / EARLIER_PHOTO).read_bytes() == photo
    # The directory the new snapshot was built in is gone too.
    assert [path.name for path in package.directory.iterdir() if path.name.startswith(".")] == []


def _photo_output() -> dict[str, Any]:
    photo = {"url": PHOTO_URI, "public_url": PHOTO_PUBLIC_URL, "mime_type": "image/png", "caption": "Sprocket"}
    return {
        "widgets": [
            {"name": "Sprocket", "photo": photo, "sheet": f'<img src="{PHOTO_PUBLIC_URL.replace("&", "&amp;")}" alt="Sprocket">'},
            {"name": "Flange", "photo": photo},
        ]
    }


class TestTakeSnapshot:
    def test_a_run_becomes_a_snapshot_with_its_files_copied_and_every_link_rewritten(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _photo_output())
        fake_api.answer(
            "POST", RESOLVE, httpx.Response(200, json={"items": [{"uri": PHOTO_URI, "url": PHOTO_FRESH_URL, "content_type": "image/png"}]})
        )
        download = mocker.patch("scripts.snapshot.download", return_value=png_bytes(width=3200, height=1600))
        stale = package.directory / "output" / "stale.png"
        stale.parent.mkdir()
        stale.write_bytes(b"from an earlier run")

        taken = take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)

        download.assert_called_once_with(PHOTO_FRESH_URL, max_bytes=50 * 1024 * 1024)
        assert fake_api.bodies("POST", RESOLVE) == [{"uris": [PHOTO_URI]}]
        written = load_snapshot(package.directory / "output.json")
        assert written == taken.snapshot
        photo = "output/widgets-0-photo.png"
        assert written.output == {
            "widgets": [
                {
                    "name": "Sprocket",
                    "photo": {"url": photo, "mime_type": "image/png", "caption": "Sprocket"},
                    "sheet": f'<img src="{photo}" alt="Sprocket">',
                },
                {"name": "Flange", "photo": {"url": photo, "mime_type": "image/png", "caption": "Sprocket"}},
            ]
        }
        assert list(written.files) == [photo]
        assert written.files[photo].resized is True
        assert Image.open(io.BytesIO((package.directory / photo).read_bytes())).size == (1600, 800)
        assert not stale.exists()
        assert (written.run.started_at.isoformat(), written.run.finished_at.isoformat()) == ("2026-09-28T09:14:02+00:00", "2026-09-28T09:14:39+00:00")
        assert written.run.route == "files"
        assert written.run.bundle_sha256 == bundle_digest(cookbook=cookbook, package=package)
        assert written.run.inputs_sha256 == inputs_digest(cookbook=cookbook, package=package)
        # The run's id and cost are printed, never written.
        raw = (package.directory / "output.json").read_text(encoding="utf-8")
        assert RUN_ID not in raw
        assert "0.0125" not in raw
        assert "pipelex-storage://" not in raw
        assert "X-Amz" not in raw
        assert taken.run.run_id == RUN_ID
        assert snapshot_problems(load_cookbook(cookbook.root)) == [
            "methods/count_words has no output.json: `make snapshot METHOD=count_words` takes it, with one paid run on production"
        ]

    def test_an_output_holding_no_file_leaves_no_output_directory(self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, {"widgets": [{"name": "Sprocket", "colour": "red"}]})
        take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert json.loads((package.directory / "output.json").read_text(encoding="utf-8"))["files"] == {}
        assert not (package.directory / "output").exists()
        assert f"POST {RESOLVE}" not in fake_api.calls()

    def test_a_client_other_than_productions_is_refused_before_any_call(self, fake_api: FakeApi, make_cookbook: MakeCookbook):
        cookbook, package = _widgets(make_cookbook)
        with pytest.raises(SnapshotError, match="unset PIPELEX_BASE_URL"):
            take_snapshot(client=fake_api.client, cookbook=cookbook, package=package)
        assert fake_api.calls() == []

    def test_a_package_that_does_not_validate_is_not_run(self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package, is_valid=False)
        with pytest.raises(SnapshotError, match="does not validate on production, so it is not run:\nverdict report"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert fake_api.calls() == []

    def test_a_stale_contract_is_refused_before_the_run(self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture):
        cookbook, package = _widgets(make_cookbook)
        assert package.contract is not None
        verdict = MethodVerdict(name=package.name, is_valid=True, report="", contract=package.contract.model_copy(update={"pipe": "widgets.other"}))
        mocker.patch("scripts.snapshot.validate_package", return_value=verdict)
        with pytest.raises(SnapshotError, match="run `make refresh` first"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert fake_api.calls() == []

    def test_an_output_of_the_wrong_shape_is_refused_and_nothing_is_written(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, {"gadgets": []})
        with pytest.raises(SnapshotError, match=f"the output of run {RUN_ID}, .* does not have its contract's shape"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert not (package.directory / "output.json").exists()

    def test_a_signed_link_the_output_holds_without_its_file_is_refused(self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, {"widgets": [{"name": "Sprocket", "link": PHOTO_PUBLIC_URL}]})
        with pytest.raises(SnapshotError, match=r"\$\.widgets\[0\]\.link holds a signed link"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert not (package.directory / "output.json").exists()

    def test_a_file_production_cannot_resolve_is_refused(self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _photo_output())
        refusal = {"uri": PHOTO_URI, "error": {"code": "forbidden", "detail": "The reference belongs to another organization."}}
        fake_api.answer("POST", RESOLVE, httpx.Response(200, json={"items": [refusal]}))
        with pytest.raises(
            SnapshotError, match=r"at \$\.widgets\[0\]\.photo\.url, .* cannot be fetched: The reference belongs to another organization"
        ):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        assert not (package.directory / "output.json").exists()


class TestAfterThePaidRun:
    """Once the run completed it is paid for: every failure names the run and how to read its output again, and leaves the previous snapshot."""

    def test_a_resolve_refused_names_the_run_and_the_route_reading_its_output(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _photo_output())
        fake_api.answer("POST", RESOLVE, httpx.Response(500, json={"detail": "The storage is unavailable."}))
        with pytest.raises(SnapshotError) as raised:
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        message = str(raised.value)
        assert f"methods/extract_widgets: run {RUN_ID}, $0.0125, 36 s completed, but its snapshot was not written" in message
        assert "/v1/resolve-storage-url/bulk answered HTTP 500" in message
        assert message.endswith(READ_AGAIN)
        assert not (package.directory / "output.json").exists()

    def test_a_download_refused_names_the_run_and_never_the_links_signature(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _photo_output())
        fake_api.answer(
            "POST", RESOLVE, httpx.Response(200, json={"items": [{"uri": PHOTO_URI, "url": PHOTO_FRESH_URL, "content_type": "image/png"}]})
        )

        def refused(url: str, *, max_bytes: int) -> bytes:
            return download(url, max_bytes=max_bytes, transport=httpx.MockTransport(lambda request: httpx.Response(403)))

        mocker.patch("scripts.snapshot.download", side_effect=refused)
        with pytest.raises(SnapshotError) as raised:
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        message = str(raised.value)
        assert f"run {RUN_ID}" in message
        assert "https://bucket.example.invalid/org_1/runs/run_0456/outputs/9a1b.png answered HTTP 403" in message
        assert "X-Amz-Signature" not in message
        assert message.endswith(READ_AGAIN)
        assert not (package.directory / "output").exists()

    def test_a_failure_while_the_new_output_is_built_leaves_the_previous_snapshot_whole(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        snapshot_json, photo = _write_earlier_snapshot(cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _two_photos_output())
        _resolves_both(fake_api)
        # The first file is fetched into the new output, and the second fails.
        refusal = HostedApiError("https://bucket.example.invalid/org_1/runs/run_0456/outputs/7c2d.png answered HTTP 403", status_code=403)
        mocker.patch("scripts.snapshot.download", side_effect=[png_bytes(width=8, height=8), refusal])
        with pytest.raises(SnapshotError, match=f"run {RUN_ID}, .* answered HTTP 403"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        _assert_earlier_snapshot_whole(package, snapshot_json=snapshot_json, photo=photo)

    def test_a_failure_while_the_new_snapshot_is_swapped_in_puts_the_previous_one_back(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture
    ):
        cookbook, package = _widgets(make_cookbook)
        snapshot_json, photo = _write_earlier_snapshot(cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, _two_photos_output())
        _resolves_both(fake_api)
        mocker.patch("scripts.snapshot.download", return_value=png_bytes(width=8, height=8))
        real_replace = os.replace

        def replace_failing_on_the_snapshot(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
            # The new `output/` is in place by then, so the previous one has to come back.
            if Path(destination).name == "output.json":
                msg = "No space left on device"
                raise OSError(msg)
            real_replace(source, destination)

        mocker.patch("scripts.snapshot.os.replace", side_effect=replace_failing_on_the_snapshot)
        with pytest.raises(SnapshotError, match=f"run {RUN_ID}, .*: No space left on device. {READ_AGAIN}"):
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        _assert_earlier_snapshot_whole(package, snapshot_json=snapshot_json, photo=photo)

    @pytest.mark.parametrize("main_stuff", [[], {"items": []}], ids=["bare", "envelope"])
    def test_an_output_holding_nothing_is_refused_since_it_shows_nothing(
        self, fake_api: FakeApi, make_cookbook: MakeCookbook, mocker: MockerFixture, main_stuff: Any
    ):
        cookbook, package = _widgets_returning_a_list(make_cookbook)
        _validates(mocker, package)
        _runs_to(fake_api, main_stuff)
        with pytest.raises(SnapshotError) as raised:
            take_snapshot(client=_production_client(fake_api), cookbook=cookbook, package=package)
        message = str(raised.value)
        assert f"the output of run {RUN_ID}, $0.0125, 36 s holds nothing to show" in message
        assert message.endswith(READ_AGAIN)
        assert not (package.directory / "output.json").exists()


def test_the_snapshot_command_needs_a_method_that_exists(make_cookbook: MakeCookbook, capsys: pytest.CaptureFixture[str]):
    from scripts.__main__ import main

    root = make_cookbook()
    assert main(["--root", str(root), "snapshot", "gone"]) == 1
    assert "no method is named `gone`: the methods are count_words, extract_widgets" in capsys.readouterr().out


def test_render_names_every_method_without_a_snapshot(make_cookbook: MakeCookbook, capsys: pytest.CaptureFixture[str]):
    from scripts.__main__ import main

    root = make_cookbook()
    (root / "templates").symlink_to(Path(__file__).resolve().parents[2] / "templates")
    assert main(["--root", str(root), "render"]) == 0
    printed = capsys.readouterr().out
    assert '· methods/count_words has no output.json yet: its page has no "What you get" until `make snapshot METHOD=count_words`' in printed


def test_the_previews_command_renders_each_recorded_document_sample_and_skips_one_without_a_record(
    make_cookbook: MakeCookbook, capsys: pytest.CaptureFixture[str]
):
    from scripts.__main__ import main

    root = make_cookbook(with_sample=True)
    pdf = io.BytesIO()
    Image.new("RGB", (300, 200), "white").save(pdf, format="PDF")
    (root / WIDGETS_SAMPLE_PATH).write_bytes(pdf.getvalue())
    make_widgets_sample_a_document(root)
    preview = "assets/extract_widgets/catalogue.preview.png"

    assert main(["--root", str(root), "previews"]) == 0
    assert f"✎ rendered {preview}" in capsys.readouterr().out
    assert main(["--root", str(root), "previews"]) == 0
    assert f"· unchanged {preview}" in capsys.readouterr().out

    (root / preview).unlink()
    drop_widgets_record(root)
    assert main(["--root", str(root), "previews"]) == 0
    assert capsys.readouterr().out == (
        f"· {WIDGETS_SAMPLE_PATH} gets no preview: its sample has no source-and-licence record "
        "under [methods.extract_widgets.samples] in cookbook.toml\n"
    )
    assert not (root / preview).exists()
