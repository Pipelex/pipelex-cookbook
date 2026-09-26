"""The output snapshot: what one production run of a method on its sample returned, committed beside the package as `output.json`.

A method's page shows its output from this file, so rendering needs no network. The snapshot records the run's times, the server, the route
(`files`, since a method on a branch cannot run by address before its release, or `address`), and two hashes: `bundle_sha256` over the
package's `.mthds` files and `inputs_sha256` over its `inputs.json` and every local asset it names. `make check-render` fails when the sample
changed since the run, since the page would then show one input beside another input's output, and only warns when the bundles changed.

A file the output holds, such as a generated image, is copied into `methods/<name>/output/`, named after the JSON path of its first reference,
and the output's references to it, the durable `pipelex-storage://` URI and the presigned link beside it, become the copy's path relative to the
package. The run id, the cost and every storage URI stay out of the repository: the writer prints them instead.

A PDF document sample kept under `assets/` gets a first-page preview beside it, `<stem>.preview.png`, which the page shows linking to the file;
a document that is not a PDF, such as an image or a Word file, cannot be rendered, so the page links it and nothing asks for its preview.
"""

import hashlib
import html
import io
import json
import mimetypes
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import cast

import pypdfium2
from PIL import Image
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, ValidationError, model_validator

from scripts.contract import Contract
from scripts.cookbook import INPUTS_FILE, Cookbook, MethodPackage, file_urls, input_content, nested_urls
from scripts.exceptions import CookbookLayoutError, HostedApiError, SnapshotError
from scripts.hosted import STORAGE_SCHEME, HostedClient, HostedRun, RunRoute, download, run_package, validate_package
from scripts.shape import LIST_MULTIPLICITIES, list_items, shape_problems

SNAPSHOT_FILE = "output.json"
# The directory beside the package holding the files the output names, which exists only when there are such files.
OUTPUT_DIR = "output"
# The only server a snapshot may come from: a page shows what production returned.
PRODUCTION_URL = "https://api.pipelex.com"
# An image the output holds is downscaled to this length on its long side, so that one snapshot does not weigh down the repository.
MAX_IMAGE_SIDE = 1600
# A PDF document sample's preview, `<stem>.preview.png` beside the sample, rendered at this length on its long side.
PREVIEW_SUFFIX = ".preview.png"
PREVIEW_LONG_SIDE = 1200
# The input kind the contract gives a document, whose sample kept under `assets/` gets a preview when it is a PDF.
DOCUMENT_KIND = "document"
# How a PDF is known: by its extension, or by the header every PDF opens with.
_PDF_SUFFIX = ".pdf"
_PDF_HEADER = b"%PDF-"
# The most a file of the output may weigh when it is fetched, before any downscaling.
MAX_FILE_BYTES = 50 * 1024 * 1024
_DEFAULT_CONTENT_TYPE = "application/octet-stream"
PUBLIC_URL_KEY = "public_url"
_URL_KEY = "url"
# The query parameters that sign a presigned link: S3's, Google Cloud Storage's and Azure's.
_SIGNATURE_PATTERN = re.compile(r"[?&](?:X-Amz-Signature|X-Amz-Credential|X-Goog-Signature|X-Goog-Credential|Signature|sig)=", re.IGNORECASE)
_NAME_UNSAFE = re.compile(r"[^A-Za-z0-9_]+")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Extensions `mimetypes` would not pick for the file's usual name.
_EXTENSIONS = {"image/jpeg": ".jpg", "text/plain": ".txt"}
_DEFAULT_EXTENSION = ".bin"
_JPEG_QUALITY = 90
# The directory the writer builds a new snapshot in, inside the package so that each rename swapping it in stays on one filesystem.
_WORK_PREFIX = ".snapshot-"
_PREVIOUS_OUTPUT = "previous-output"


class SnapshotRoute(StrEnum):
    """How the snapshot's run reached the method: from the package's files, or by its address at a tag."""

    FILES = "files"
    ADDRESS = "address"


class SnapshotRun(BaseModel):
    """The run the snapshot was taken from, without its id or its cost, which stay out of the repository."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    started_at: AwareDatetime
    finished_at: AwareDatetime
    server: str = Field(description="The hosted API that ran it, always production")
    route: SnapshotRoute
    method_ref: str | None = Field(description="The address the run named, for an address run")
    commit_sha: str | None = Field(description="The commit the address resolved to, for an address run")
    bundle_sha256: str = Field(description="The hash of the package's `.mthds` files when the run was taken")
    inputs_sha256: str = Field(description="The hash of `inputs.json` and every local asset it names when the run was taken")

    @model_validator(mode="after")
    def _check_route(self) -> "SnapshotRun":
        if self.server != PRODUCTION_URL:
            msg = f"a snapshot comes from production, {PRODUCTION_URL}, and this one names {self.server}"
            raise ValueError(msg)
        if self.finished_at < self.started_at:
            msg = "the run finished before it started"
            raise ValueError(msg)
        match self.route:
            case SnapshotRoute.ADDRESS:
                if self.method_ref is None or self.commit_sha is None:
                    msg = "an address run names its `method_ref` and the `commit_sha` it resolved to"
                    raise ValueError(msg)
            case SnapshotRoute.FILES:
                if self.method_ref is not None or self.commit_sha is not None:
                    msg = "a run from the package's files names no `method_ref` and no `commit_sha`"
                    raise ValueError(msg)
        return self

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()


class SnapshotFile(BaseModel):
    """A file of the output, copied into `output/`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sha256: str
    content_type: str
    resized: bool = Field(default=False, description="Whether the writer downscaled the image, written only when it did")


class OutputSnapshot(BaseModel):
    """The committed `output.json` of a package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pipe: str = Field(description="The main pipe the run ran, as `contract.json` names it")
    concept: str = Field(description="The output concept, as `contract.json` names it")
    run: SnapshotRun
    output: JsonValue = Field(description="The run's `main_stuff`, its file references rewritten to the copies' paths")
    files: dict[str, SnapshotFile] = Field(default_factory=dict, description="Each copied file, by its path relative to the package")

    def to_json(self) -> str:
        data: dict[str, JsonValue] = {
            "pipe": self.pipe,
            "concept": self.concept,
            "run": cast("JsonValue", self.run.model_dump(mode="json")),
            "output": self.output,
            "files": {path: cast("JsonValue", entry.model_dump(mode="json", exclude_defaults=True)) for path, entry in self.files.items()},
        }
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def snapshot_path(package: MethodPackage) -> Path:
    return package.directory / SNAPSHOT_FILE


def load_snapshot(path: Path) -> OutputSnapshot:
    """Read a committed `output.json`.

    Raises:
        CookbookLayoutError: The file is not a snapshot.
    """
    try:
        return OutputSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        msg = f"{path}: not an output snapshot; take it again with `make snapshot METHOD={path.parent.name}`:\n{exc}"
        raise CookbookLayoutError(msg) from exc


def read_snapshot(package: MethodPackage) -> OutputSnapshot | None:
    """The package's snapshot, or None when it has none yet.

    Raises:
        CookbookLayoutError: The file is there and is not a snapshot.
    """
    path = snapshot_path(package)
    return load_snapshot(path) if path.is_file() else None


# ── The two hashes ───────────────────────────────────────────────────


def files_digest(*, root: Path, paths: Sequence[Path]) -> str:
    """A sha256 over the sorted lines `<path from the repository root>\\0<sha256 of the file>\\n`, one per file."""
    lines = sorted(f"{path.relative_to(root).as_posix()}\0{sha256_of(path.read_bytes())}\n" for path in paths)
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_digest(*, cookbook: Cookbook, package: MethodPackage) -> str:
    """The hash of the package's `.mthds` files, which says whether the method changed since the snapshot was taken."""
    return files_digest(root=cookbook.root, paths=package.bundle_paths())


def sample_files(*, cookbook: Cookbook, package: MethodPackage) -> list[Path]:
    """The local files the sample names: every file its `inputs.json` links by a raw URL into this repository, at any depth, in input order.

    The files are those a run uploads from this checkout, read by the same walk of the inputs (`nested_urls`), so that the hash covers every
    file the run is given, a file nested in a structured input included.

    Raises:
        CookbookLayoutError: A URL into this repository names a file this checkout does not hold.
    """
    found: list[Path] = []
    for url in nested_urls(package.inputs):
        path = _sample_file(cookbook=cookbook, package=package, url=url)
        if path is not None and path not in found:
            found.append(path)
    return found


def _sample_file(*, cookbook: Cookbook, package: MethodPackage, url: str) -> Path | None:
    """The file of this checkout a sample's URL names, under the cookbook's root as it was loaded, or None for a URL hosted elsewhere.

    Raises:
        CookbookLayoutError: The URL points into this repository, but names no file this checkout holds.
    """
    try:
        local_file = cookbook.local_file_of(url)
    except CookbookLayoutError as exc:
        msg = f"{package.directory.relative_to(cookbook.root)}/{INPUTS_FILE} links {url}, and {exc}"
        raise CookbookLayoutError(msg) from exc
    return None if local_file is None else cookbook.root / local_file.path.relative_to(cookbook.root.resolve())


def inputs_digest(*, cookbook: Cookbook, package: MethodPackage) -> str:
    """The hash of the sample: `inputs.json` and every local asset it names, which says whether the sample changed since the snapshot.

    Raises:
        CookbookLayoutError: A URL into this repository names a file this checkout does not hold.
    """
    return files_digest(root=cookbook.root, paths=[package.directory / INPUTS_FILE, *sample_files(cookbook=cookbook, package=package)])


# ── The document previews ────────────────────────────────────────────


def preview_path(sample: Path) -> Path:
    """Where a document sample's first-page preview lives: beside it, as `<stem>.preview.png`."""
    return sample.with_name(f"{sample.stem}{PREVIEW_SUFFIX}")


def document_samples(*, cookbook: Cookbook, package: MethodPackage) -> list[Path]:
    """The local PDF files of the inputs the contract calls documents and whose source-and-licence record is written: those the page previews.

    A document without its record never gets a preview, since its provenance is not settled: it may hold a real person's data, which the
    page must not show. A document that is not a PDF gets none either, since only a PDF can be rendered.

    Raises:
        CookbookLayoutError: A URL into this repository names a file this checkout does not hold.
    """
    return [path for input_name, path in _local_documents(cookbook=cookbook, package=package) if input_name in package.editorial.samples]


def unrecorded_documents(*, cookbook: Cookbook, package: MethodPackage) -> list[Path]:
    """The local PDF document samples without their source-and-licence record, which get no preview until it is written.

    Raises:
        CookbookLayoutError: A URL into this repository names a file this checkout does not hold.
    """
    return [path for input_name, path in _local_documents(cookbook=cookbook, package=package) if input_name not in package.editorial.samples]


def _local_documents(*, cookbook: Cookbook, package: MethodPackage) -> list[tuple[str, Path]]:
    """Each input the contract calls a document with the local file of its sample, for every PDF it names in this repository."""
    contract = package.contract
    if contract is None:
        return []
    kinds = {contract_input.name: contract_input.kind for contract_input in contract.inputs}
    found: list[tuple[str, Path]] = []
    for input_name, value in package.inputs.items():
        if kinds.get(input_name) != DOCUMENT_KIND:
            continue
        for url in file_urls(input_content(value)):
            path = _sample_file(cookbook=cookbook, package=package, url=url)
            if path is not None and is_pdf(path):
                found.append((input_name, path))
    return found


def is_pdf(path: Path) -> bool:
    """Whether a file is a PDF, the one kind of document a preview can be rendered from: by its `.pdf` extension, or by the PDF header."""
    if path.suffix.lower() == _PDF_SUFFIX:
        return True
    with path.open("rb") as document:
        return document.read(len(_PDF_HEADER)) == _PDF_HEADER


def render_preview(document: Path) -> bytes:
    """Render a PDF's first page as a PNG, its long side `PREVIEW_LONG_SIDE` pixels.

    Raises:
        CookbookLayoutError: The file is not a PDF pypdfium2 can open, or has no page.
    """
    try:
        pdf = pypdfium2.PdfDocument(document)
    except pypdfium2.PdfiumError as exc:
        msg = f"{document} is not a PDF that can be previewed: {exc}"
        raise CookbookLayoutError(msg) from exc
    try:
        if len(pdf) == 0:
            msg = f"{document} has no page to preview"
            raise CookbookLayoutError(msg)
        page = pdf[0]
        width, height = page.get_size()
        # pypdfium2 leaves its rendering calls untyped: the page renders to a bitmap, which converts to a Pillow image.
        bitmap = page.render(scale=PREVIEW_LONG_SIDE / max(width, height))  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        image = cast("Image.Image", bitmap.to_pil())  # pyright: ignore[reportUnknownMemberType]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
    finally:
        pdf.close()


def write_previews(*, cookbook: Cookbook, package: MethodPackage) -> list[Path]:
    """Render the preview of every document sample `document_samples` names, and return those written because they were missing or differed.

    A preview that already holds what the rendering gives is left as it is. Rendering needs no key and no network.

    Raises:
        CookbookLayoutError: The sample names a file this checkout does not hold, or a document sample cannot be previewed.
    """
    written: list[Path] = []
    for document in document_samples(cookbook=cookbook, package=package):
        path = preview_path(document)
        rendered = render_preview(document)
        if path.is_file() and path.read_bytes() == rendered:
            continue
        path.write_bytes(rendered)
        written.append(path)
    return written


# ── The output's files ───────────────────────────────────────────────


class StorageReference(BaseModel):
    """A file the output holds: its durable reference, where it was first found, and the presigned links the output carries for it."""

    model_config = ConfigDict(frozen=True)

    uri: str
    segments: list[str | int] = Field(description="The JSON path of its first occurrence, as keys and indexes from the output's root")
    public_urls: list[str] = Field(default_factory=list[str])

    @property
    def found_at(self) -> str:
        return json_path(self.segments)


def json_path(segments: Sequence[str | int]) -> str:
    """A path rooted at `$`: an identifier key as `.key`, any other key as `["…"]`, an index as `[n]`."""
    parts = ["$"]
    for segment in segments:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        elif _IDENTIFIER.match(segment):
            parts.append(f".{segment}")
        else:
            parts.append(f"[{json.dumps(segment, ensure_ascii=False)}]")
    return "".join(parts)


def is_storage_reference(value: str) -> bool:
    return value.startswith(STORAGE_SCHEME) and len(value) > len(STORAGE_SCHEME)


def storage_references(output: JsonValue) -> list[StorageReference]:
    """Every file the output holds, once each, in the order of its first occurrence, with the presigned links beside its references."""
    first_seen: dict[str, list[str | int]] = {}
    public_urls: dict[str, list[str]] = {}

    def visit(node: JsonValue, segments: list[str | int]) -> None:
        if isinstance(node, str):
            if is_storage_reference(node) and node not in first_seen:
                first_seen[node] = segments
            return
        if isinstance(node, list):
            for index, item in enumerate(node):
                visit(item, [*segments, index])
            return
        if isinstance(node, dict):
            uri = node.get(_URL_KEY)
            public_url = node.get(PUBLIC_URL_KEY)
            if isinstance(uri, str) and is_storage_reference(uri) and isinstance(public_url, str) and public_url:
                links = public_urls.setdefault(uri, [])
                if public_url not in links:
                    links.append(public_url)
            for key, item in node.items():
                visit(item, [*segments, key])

    visit(output, [])
    return [StorageReference(uri=uri, segments=segments, public_urls=public_urls.get(uri, [])) for uri, segments in first_seen.items()]


def file_name(*, segments: Sequence[str | int], content_type: str | None, uri: str) -> str:
    """Name a copied file after the JSON path of its first reference: the trailing `url` dropped, every key and index joined by `-`.

    `$.items[0].illustrations[2].image.url` names `items-0-illustrations-2-image.png`, and an output that is itself a file names `output`
    with its extension.
    """
    parts = list(segments)
    if parts and parts[-1] == _URL_KEY:
        parts.pop()
    words = [str(part) if isinstance(part, int) else _NAME_UNSAFE.sub("_", part).strip("_") for part in parts]
    stem = "-".join(word for word in words if word) or "output"
    return f"{stem}{file_extension(content_type=content_type, uri=uri)}"


def file_extension(*, content_type: str | None, uri: str) -> str:
    """The extension of a file's content type, else of its storage key, else `.bin`."""
    if content_type:
        media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
        extension = _EXTENSIONS.get(media_type) or mimetypes.guess_extension(media_type)
        if extension:
            return extension
    suffix = PurePosixPath(uri.removeprefix(STORAGE_SCHEME)).suffix
    return suffix.lower() if suffix else _DEFAULT_EXTENSION


def rewrite_output(output: JsonValue, *, replacements: Mapping[str, str]) -> JsonValue:
    """The output with every `public_url` key removed and every reference replaced, whole or inside a longer text such as HTML.

    `replacements` maps each storage URI and each presigned link to the copy's path; a link written into HTML with its ampersands escaped is
    replaced too.
    """
    pairs: list[tuple[str, str]] = []
    for old, new in replacements.items():
        pairs.append((old, new))
        escaped = html.escape(old, quote=True)
        if escaped != old:
            pairs.append((escaped, new))
    # The longest first, so a link is never cut by a shorter one it contains.
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)

    def rewrite(node: JsonValue) -> JsonValue:
        if isinstance(node, str):
            text = node
            for old, new in pairs:
                if old in text:
                    text = text.replace(old, new)
            return text
        if isinstance(node, list):
            return [rewrite(item) for item in node]
        if isinstance(node, dict):
            return {key: rewrite(item) for key, item in node.items() if key != PUBLIC_URL_KEY}
        return node

    return rewrite(output)


def leftover_links(output: JsonValue) -> list[str]:
    """Where the output still holds a storage reference or a signed link, which must never reach the repository."""
    found: list[str] = []

    def visit(node: JsonValue, segments: list[str | int]) -> None:
        if isinstance(node, str):
            if STORAGE_SCHEME in node:
                found.append(f"{json_path(segments)} holds a {STORAGE_SCHEME} reference")
            elif _SIGNATURE_PATTERN.search(node):
                found.append(f"{json_path(segments)} holds a signed link")
        elif isinstance(node, list):
            for index, item in enumerate(node):
                visit(item, [*segments, index])
        elif isinstance(node, dict):
            for key, item in node.items():
                if key == PUBLIC_URL_KEY:
                    found.append(f"{json_path([*segments, key])} is a presigned link")
                visit(item, [*segments, key])

    visit(output, [])
    return found


def fit_image(data: bytes, *, content_type: str | None) -> tuple[bytes, bool]:
    """Downscale an image longer than `MAX_IMAGE_SIDE` on its long side, keeping its format and its proportions.

    Returns:
        The bytes to copy, and whether they were downscaled. Anything that is not an image Pillow reads is returned as it is, and so is an
        animated image, such as an animated GIF or WebP, whose downscaling would keep only its first frame.
    """
    if not (content_type or "").lower().startswith("image/"):
        return data, False
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (OSError, Image.DecompressionBombError):
        return data, False
    if getattr(image, "is_animated", False):
        return data, False
    width, height = image.size
    if max(width, height) <= MAX_IMAGE_SIDE:
        return data, False
    image_format = image.format or "PNG"
    ratio = MAX_IMAGE_SIDE / max(width, height)
    # Pillow types the size loosely, which strict pyright reads as partly unknown.
    resized = image.resize((max(1, round(width * ratio)), max(1, round(height * ratio))), Image.Resampling.LANCZOS)  # pyright: ignore[reportUnknownMemberType]
    buffer = io.BytesIO()
    if image_format == "JPEG":
        resized.save(buffer, format=image_format, quality=_JPEG_QUALITY)
    else:
        resized.save(buffer, format=image_format)
    return buffer.getvalue(), True


# ── The writer ───────────────────────────────────────────────────────


class TakenSnapshot(BaseModel):
    """What `make snapshot` did: the snapshot it wrote, the run it took it from, and the previews it wrote because they were missing or differed."""

    model_config = ConfigDict(frozen=True)

    snapshot: OutputSnapshot
    run: HostedRun
    previews: list[Path]


def take_snapshot(*, client: HostedClient, cookbook: Cookbook, package: MethodPackage) -> TakenSnapshot:
    """Run a method once on production on its sample and write its output snapshot. The run spends inference credit.

    Everything that can fail for free is done first: the client must be production's, the package must validate and its validation must give
    the committed contract, and every PDF document sample's preview is rendered. Then the method runs from the package's files, the output
    must have its contract's shape and hold something to show, each file it holds is fetched through the storage resolve route, downscaled
    when it is a large image, and copied into a new `output/`, and every reference to it is rewritten; nothing is written while a storage
    reference or a signed link is left. The new `output/` and `output.json` are built complete beside the package's before either replaces
    its predecessor, so a failure at any point leaves the previous snapshot whole.

    Once the run completed, it is paid for, so every error raised after it names the run, its cost, and the route reading its output again.

    Raises:
        SnapshotError: The client is not production's, the package does not validate or its contract is stale, the output does not have its
            contract's shape or holds nothing, a file could not be resolved or fetched, a reference or a signed link is left in the output,
            or the snapshot could not be written.
        CookbookLayoutError: The sample names a file this checkout does not hold, or a document sample cannot be previewed.
        HostedApiError: A call to production failed before the run completed.
        HostedRunError: The run ended without a result.
    """
    package_dir = package.directory.relative_to(cookbook.root)
    if client.base_url.rstrip("/") != PRODUCTION_URL:
        msg = f"a snapshot shows what production returned, and this client calls {client.base_url}: unset PIPELEX_BASE_URL"
        raise SnapshotError(msg)
    contract = package.contract
    if contract is None:
        msg = f"{package_dir} has no contract snapshot yet: run `make refresh` before taking its output snapshot"
        raise SnapshotError(msg)
    verdict = validate_package(client=client, package=package)
    if not verdict.is_valid:
        msg = f"{package_dir} does not validate on production, so it is not run:\n{verdict.report}"
        raise SnapshotError(msg)
    if verdict.contract != contract:
        msg = f"{package_dir}/contract.json is not the contract production gives the package's files: run `make refresh` first"
        raise SnapshotError(msg)
    previews = write_previews(cookbook=cookbook, package=package)
    bundle_sha256 = bundle_digest(cookbook=cookbook, package=package)
    inputs_sha256 = inputs_digest(cookbook=cookbook, package=package)

    run = run_package(client=client, cookbook=cookbook, package=package)
    problems = shape_problems(contract=contract, output=run.main_stuff)
    if problems:
        msg = (
            f"{package_dir}: the output of {run.summary()} does not have its contract's shape, so no snapshot was written:\n- "
            + "\n- ".join(problems)
            + f"\n{_read_again(run)}"
        )
        raise SnapshotError(msg)
    if _holds_nothing(contract=contract, output=run.main_stuff):
        msg = (
            f"{package_dir}: the output of {run.summary()} holds nothing to show, and an example that shows nothing is no example, "
            f"so no snapshot was written. {_read_again(run)}"
        )
        raise SnapshotError(msg)
    try:
        snapshot = _write_snapshot(
            client=client,
            package=package,
            package_dir=package_dir,
            contract=contract,
            run=run,
            bundle_sha256=bundle_sha256,
            inputs_sha256=inputs_sha256,
        )
    except (HostedApiError, ValidationError, OSError) as exc:
        msg = (
            f"{package_dir}: {run.summary()} completed, but its snapshot was not written, and the previous one is left whole: {exc}. "
            f"{_read_again(run)}"
        )
        raise SnapshotError(msg) from exc
    return TakenSnapshot(snapshot=snapshot, run=run, previews=previews)


def _holds_nothing(*, contract: Contract, output: JsonValue) -> bool:
    """Whether an output of its contract's shape holds nothing a page could show: a list output with no item, or an object with no field."""
    if contract.output.multiplicity in LIST_MULTIPLICITIES:
        return list_items(output) == []
    return output == {}


def _read_again(run: HostedRun) -> str:
    """What an error raised once a run completed says of it: that its output is paid for, and how to read it again by the run's id."""
    return f"The output is paid for: GET /v1/runs/{run.run_id}/results reads it again"


def _write_snapshot(
    *,
    client: HostedClient,
    package: MethodPackage,
    package_dir: Path,
    contract: Contract,
    run: HostedRun,
    bundle_sha256: str,
    inputs_sha256: str,
) -> OutputSnapshot:
    """Fetch the files a completed run's output holds, and write its snapshot in place of the package's previous one.

    The new `output/` and `output.json` are built in a directory of their own inside the package, then swapped in by renames, so that a
    failure while they are built, or while they are swapped in, leaves the previous snapshot whole.

    Raises:
        SnapshotError: A file could not be resolved, or a reference or a signed link is left in the output.
        HostedApiError: A file could not be resolved or fetched.
        ValidationError: The run's times or route do not make a snapshot.
        OSError: A file could not be written.
    """
    work = Path(tempfile.mkdtemp(prefix=_WORK_PREFIX, dir=package.directory))
    try:
        new_output_dir = work / OUTPUT_DIR
        new_output_dir.mkdir()
        replacements, entries = _fetch_files(client=client, output=run.main_stuff, staging=new_output_dir, run=run)
        output = rewrite_output(run.main_stuff, replacements=replacements)
        leftovers = leftover_links(output)
        if leftovers:
            msg = (
                f"{package_dir}: the output of {run.summary()} still holds links that must not reach the repository:\n- "
                + "\n- ".join(leftovers)
                + f"\n{_read_again(run)}"
            )
            raise SnapshotError(msg)
        snapshot = OutputSnapshot(
            pipe=contract.pipe,
            concept=contract.output.concept,
            run=SnapshotRun(
                started_at=_utc(run.started_at),
                finished_at=_utc(run.finished_at),
                server=PRODUCTION_URL,
                route=SnapshotRoute(run.route.value),
                method_ref=run.method_ref if run.route == RunRoute.ADDRESS else None,
                commit_sha=run.commit_sha if run.route == RunRoute.ADDRESS else None,
                bundle_sha256=bundle_sha256,
                inputs_sha256=inputs_sha256,
            ),
            output=output,
            files=entries,
        )
        (work / SNAPSHOT_FILE).write_text(snapshot.to_json(), encoding="utf-8")
        if not entries:
            new_output_dir.rmdir()
        _swap_in(package=package, work=work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return snapshot


def _swap_in(*, package: MethodPackage, work: Path) -> None:
    """Replace the package's `output/` and `output.json` with those `work` holds, complete, putting the previous `output/` back on a failure.

    The package loses its `output/` when `work` holds none, since a snapshot replaces `output/` as a whole. Each rename is atomic, and the
    previous `output/` is moved aside into `work`, so that a rename failing midway undoes those made before it.

    Raises:
        OSError: A rename failed; the previous snapshot is in place again.
    """
    output_dir = package.directory / OUTPUT_DIR
    new_output_dir = work / OUTPUT_DIR
    previous_output_dir = work / _PREVIOUS_OUTPUT
    moved_previous = False
    moved_new = False
    try:
        if output_dir.exists():
            os.replace(output_dir, previous_output_dir)
            moved_previous = True
        if new_output_dir.exists():
            os.replace(new_output_dir, output_dir)
            moved_new = True
        os.replace(work / SNAPSHOT_FILE, snapshot_path(package))
    except OSError:
        if moved_new:
            os.replace(output_dir, new_output_dir)
        if moved_previous:
            os.replace(previous_output_dir, output_dir)
        raise


def _fetch_files(*, client: HostedClient, output: JsonValue, staging: Path, run: HostedRun) -> tuple[dict[str, str], dict[str, SnapshotFile]]:
    """Fetch every file the output holds into `staging`, and say what each reference becomes and what `files` records.

    Raises:
        SnapshotError: The API resolved no link for a reference.
        HostedApiError: A file could not be fetched.
    """
    references = storage_references(output)
    if not references:
        return {}, {}
    resolved = {item.uri: item for item in client.resolve_storage_urls(uris=[reference.uri for reference in references])}
    replacements: dict[str, str] = {}
    entries: dict[str, SnapshotFile] = {}
    for reference in references:
        item = resolved.get(reference.uri)
        if item is None or item.url is None:
            reason = item.error.detail if item is not None and item.error is not None else "no link was resolved for it"
            msg = f"the file the output holds at {reference.found_at}, from {run.summary()}, cannot be fetched: {reason}. {_read_again(run)}"
            raise SnapshotError(msg)
        content_type = item.content_type or mimetypes.guess_type(reference.uri.removeprefix(STORAGE_SCHEME))[0] or _DEFAULT_CONTENT_TYPE
        data, resized = fit_image(download(item.url, max_bytes=MAX_FILE_BYTES), content_type=content_type)
        name = _unique_name(file_name(segments=reference.segments, content_type=content_type, uri=reference.uri), taken=entries)
        (staging / name).write_bytes(data)
        relative = f"{OUTPUT_DIR}/{name}"
        entries[relative] = SnapshotFile(sha256=sha256_of(data), content_type=content_type, resized=resized)
        replacements[reference.uri] = relative
        for public_url in reference.public_urls:
            replacements[public_url] = relative
    return replacements, entries


def _unique_name(name: str, *, taken: Mapping[str, SnapshotFile]) -> str:
    """The name, or the name with `-2`, `-3` and so on before its extension when another file of the output already has it."""
    path = PurePosixPath(name)
    candidate = name
    index = 2
    while f"{OUTPUT_DIR}/{candidate}" in taken:
        candidate = f"{path.stem}-{index}{path.suffix}"
        index += 1
    return candidate


def _utc(moment: datetime) -> datetime:
    """A moment in UTC, to the second, as the snapshot records it; a naive one is read as UTC."""
    aware = moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)
    return aware.astimezone(UTC).replace(microsecond=0)
