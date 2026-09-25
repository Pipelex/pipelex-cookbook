"""Tests of `scripts/sdk/recipe_codegen.py`, run as the Makefile runs it, with `uv run --script`, from the root of a small cookbook.

The script runs beside `pipelex-sdk`, which cannot be installed with the runtime this repository pins, so it is run in its own environment,
which `uv` installs from the network the first time. It calls a local stand-in for the hosted API rather than production: the stand-in keeps
every request body it reads, and answers `POST /v1/codegen` with the types of a committed recipe tree, whose lock vouches for them, so a tree
the script writes from that answer passes the offline check. No key is read: the script is given a made-up one.
"""

import json
import os
import shutil
import subprocess
import threading
import tomllib
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from typing_extensions import override

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "sdk" / "recipe_codegen.py"
# The committed recipe trees whose stamped files and lock stand in for what codegen answers, by target.
ANSWER_TREES = {
    "python-pydantic": REPO_ROOT / "recipes" / "code" / "python" / "csv-batch" / "generated" / "invoice_extraction",
    "ts-zod": REPO_ROOT / "recipes" / "code" / "typescript" / "upload-grant" / "generated" / "extract_gantt",
}
BUNDLES = {"methods/extract_widgets/bundle.mthds": 'domain = "widgets"\n', "methods/extract_widgets/pages.mthds": 'domain = "pages"\n'}
ADDRESS = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
OTHER_FINGERPRINT = "0" * 64

pytestmark = [
    pytest.mark.skipif(shutil.which("uv") is None, reason="the script runs through `uv run --script`"),
    # The script's environment is installed from the network the first time, which a sandbox without one cannot do.
    pytest.mark.codex_disabled,
]


def _answer(target: str) -> dict[str, Any]:
    """A valid `/v1/codegen` report for `target`, made of a committed recipe tree's stamped files and lock."""
    tree = ANSWER_TREES[target]
    lock = (tree / "codegen.lock").read_text(encoding="utf-8")
    locked = tomllib.loads(lock)
    return {
        "is_valid": True,
        "kind": "types",
        "target": target,
        "crate_fingerprint": locked["crate_fingerprint"],
        "engine_version": locked["engine_version"],
        "artifacts": [
            {"path": artifact["path"], "content": (tree / artifact["path"]).read_text(encoding="utf-8")} for artifact in locked["artifacts"]
        ],
        "lock": lock,
        "lock_filename": "codegen.lock",
        "message": "Generated.",
    }


class FakeCodegen:
    """A local stand-in for the hosted API: it answers `POST /v1/codegen` with a committed tree's types, and keeps every body it read."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.crate_fingerprint: str | None = None
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body: dict[str, Any] = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
                fake.requests.append(body)
                if self.path != "/v1/codegen":
                    self._answer(404, {"detail": f"no route {self.path}"})
                    return
                answer = _answer(str(body["target"]))
                if fake.crate_fingerprint is not None:
                    answer["crate_fingerprint"] = fake.crate_fingerprint
                self._answer(200, answer)

            def _answer(self, status: int, body: dict[str, Any]) -> None:
                payload = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            @override
            def log_message(self, format: str, *args: Any) -> None:
                """Keep the test's output free of one access line per request."""
                del format, args

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host!s}:{port}"


@pytest.fixture
def fake_codegen() -> Iterator[FakeCodegen]:
    fake = FakeCodegen()
    thread = threading.Thread(target=fake.server.serve_forever, daemon=True)
    thread.start()
    yield fake
    fake.server.shutdown()
    fake.server.server_close()
    thread.join()


def _cookbook(root: Path) -> Path:
    """A cookbook root holding one package's bundles, as a files-form sidecar names them."""
    for relative_path, content in BUNDLES.items():
        (root / relative_path).parent.mkdir(parents=True, exist_ok=True)
        (root / relative_path).write_text(content, encoding="utf-8")
    return root


def _tree(root: Path, *, language: str, method: dict[str, Any], target: str) -> Path:
    """A generated tree under the page snippets, holding only its sidecar, as `make render` leaves it."""
    tree = root / "tests" / "snippets" / "extract_widgets" / language / "generated" / "extract_widgets"
    tree.mkdir(parents=True)
    (tree / "sources.json").write_text(json.dumps({"generator": "pipelex-cookbook", "method": method, "target": target}), encoding="utf-8")
    return tree


def _run(root: Path, *arguments: str, base_url: str = "http://127.0.0.1:9") -> subprocess.CompletedProcess[str]:
    """Run the script from `root`, as the Makefile runs it from the repository's, against `base_url` with a made-up key."""
    environment = {name: value for name, value in os.environ.items() if not name.startswith("PIPELEX_")}
    environment |= {"PIPELEX_API_KEY": "not-a-real-key", "PIPELEX_BASE_URL": base_url, "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )


def _relative(root: Path, tree: Path) -> str:
    return tree.relative_to(root).as_posix()


class TestFilesForm:
    def test_generate_sends_the_files_contents_and_writes_a_tree_the_offline_check_trusts(self, tmp_path: Path, fake_codegen: FakeCodegen):
        root = _cookbook(tmp_path)
        tree = _tree(root, language="python", method={"files": list(BUNDLES)}, target="python-pydantic")

        generated = _run(root, "generate", _relative(root, tree), base_url=fake_codegen.base_url)
        assert generated.returncode == 0, generated.stderr
        assert fake_codegen.requests == [
            {
                "files": [{"content": content, "source": relative_path} for relative_path, content in BUNDLES.items()],
                "kind": "types",
                "target": "python-pydantic",
            }
        ]
        assert "methods/extract_widgets/bundle.mthds and methods/extract_widgets/pages.mthds (python-pydantic)" in generated.stdout
        assert sorted(path.name for path in tree.iterdir()) == ["__init__.py", "codegen.lock", "models.py", "sources.json"]
        assert (tree.parent / "__init__.py").is_file()

        checked = _run(root, "check", _relative(root, tree))
        assert checked.returncode == 0, checked.stderr
        assert "is current with its lock" in checked.stdout

    def test_a_typescript_tree_is_generated_from_its_files_too(self, tmp_path: Path, fake_codegen: FakeCodegen):
        root = _cookbook(tmp_path)
        tree = _tree(root, language="typescript", method={"files": ["methods/extract_widgets/bundle.mthds"]}, target="ts-zod")

        generated = _run(root, "generate", _relative(root, tree), base_url=fake_codegen.base_url)
        assert generated.returncode == 0, generated.stderr
        [request] = fake_codegen.requests
        assert request["files"] == [{"content": BUNDLES["methods/extract_widgets/bundle.mthds"], "source": "methods/extract_widgets/bundle.mthds"}]
        assert "method_ref" not in request
        assert sorted(path.name for path in tree.iterdir()) == ["binder.ts", "codegen.lock", "sources.json", "types.ts"]

    def test_verify_compares_the_lock_with_the_crate_codegen_makes_of_the_files_today(self, tmp_path: Path, fake_codegen: FakeCodegen):
        root = _cookbook(tmp_path)
        tree = _tree(root, language="python", method={"files": list(BUNDLES)}, target="python-pydantic")
        assert _run(root, "generate", _relative(root, tree), base_url=fake_codegen.base_url).returncode == 0

        verified = _run(root, "verify", _relative(root, tree), base_url=fake_codegen.base_url)
        assert verified.returncode == 0, verified.stderr
        assert "as codegen reads it today" in verified.stdout

        fake_codegen.crate_fingerprint = OTHER_FINGERPRINT
        edited = _run(root, "verify", _relative(root, tree), base_url=fake_codegen.base_url)
        assert edited.returncode == 1
        assert f"while codegen makes crate {OTHER_FINGERPRINT} of methods/extract_widgets/bundle.mthds and" in edited.stderr
        assert "run `make refresh`" in edited.stderr
        assert all("files" in request and "method_ref" not in request for request in fake_codegen.requests)


class TestAddressForm:
    def test_generate_still_sends_a_recipes_address(self, tmp_path: Path, fake_codegen: FakeCodegen):
        tree = _tree(tmp_path, language="python", method={"method_ref": ADDRESS}, target="python-pydantic")

        generated = _run(tmp_path, "generate", _relative(tmp_path, tree), base_url=fake_codegen.base_url)
        assert generated.returncode == 0, generated.stderr
        assert fake_codegen.requests == [{"method_ref": ADDRESS, "kind": "types", "target": "python-pydantic"}]


class TestSidecarRefusals:
    @pytest.mark.parametrize(
        ("method", "problem"),
        [
            ({"method_ref": ADDRESS, "files": ["methods/extract_widgets/bundle.mthds"]}, "must name exactly one of `method_ref`"),
            ({}, "must name exactly one of `method_ref`"),
            ({"files": []}, "`method.files` names no file"),
            ({"files": ["assets/extract_widgets/bundle.mthds"]}, "which is not the path of a .mthds file under methods/"),
            ({"files": ["methods/extract_widgets/inputs.json"]}, "which is not the path of a .mthds file under methods/"),
            ({"files": ["methods/../bundle.mthds"]}, "which is not the path of a .mthds file under methods/"),
            ({"files": ["/methods/extract_widgets/bundle.mthds"]}, "which is not the path of a .mthds file under methods/"),
            ({"files": ["methods/extract_widgets/missing.mthds"]}, "which is not a file here: run this script from the repository root"),
            ({"method_ref": "github.com/Pipelex/methods/invoice_extraction"}, "must be an address pinned to a tag"),
        ],
    )
    def test_a_sidecar_that_names_no_single_source_it_can_read_has_no_verdict(self, tmp_path: Path, method: dict[str, Any], problem: str):
        root = _cookbook(tmp_path)
        tree = _tree(root, language="python", method=method, target="python-pydantic")

        checked = _run(root, "check", _relative(root, tree))
        assert checked.returncode == 2
        assert problem in checked.stderr
