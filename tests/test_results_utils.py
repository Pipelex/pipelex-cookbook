import os
from pathlib import Path
from typing import List

from utils import results_utils


def test_get_results_dir_path_creates_incremental_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(results_utils, "SAMPLE_RESULTS_DIR_PATH", str(tmp_path))

    first_dir = results_utils.get_results_dir_path("sample")
    second_dir = results_utils.get_results_dir_path("sample")

    assert Path(first_dir).is_dir()
    assert Path(second_dir).is_dir()
    assert first_dir.endswith("sample_01")
    assert second_dir.endswith("sample_02")


def test_get_results_file_path_increments_when_file_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(results_utils, "SAMPLE_RESULTS_DIR_PATH", str(tmp_path))
    monkeypatch.setattr(results_utils, "pretty_print", lambda *_, **__: None)

    results_utils.output_result(
        sample_name="sample",
        title="title",
        file_name="out.txt",
        content="data",
    )

    expected_first = tmp_path / "sample" / "out_01.txt"
    assert expected_first.is_file()

    next_path = results_utils.get_results_file_path("sample", "out.txt")
    assert next_path.endswith("out_02.txt")


def test_output_result_writes_file_and_prints(tmp_path, monkeypatch):
    monkeypatch.setattr(results_utils, "SAMPLE_RESULTS_DIR_PATH", str(tmp_path))
    captured: List[str] = []

    def fake_pretty_print(path: str, title: str) -> None:
        captured.append(path)
        captured.append(title)

    monkeypatch.setattr(results_utils, "pretty_print", fake_pretty_print)

    results_utils.output_result(
        sample_name="sample",
        title="Title",
        file_name="result.txt",
        content="hello",
    )

    expected_file = tmp_path / "sample" / "result_01.txt"
    assert expected_file.read_text() == "hello"
    assert captured == [f"file://{os.path.abspath(expected_file)}", "Title"]
