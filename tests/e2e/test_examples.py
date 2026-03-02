import subprocess

import pytest
from pipelex.system.environment import get_optional_env


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestExamples:
    def test_extract_dpe(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_dpe/",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_gantt(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_gantt/bundle.mthds",
                "-i",
                "examples/b_basics/document_extract/extract_gantt/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_generic(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_generic/bundle.mthds",
                "-i",
                "examples/b_basics/document_extract/extract_generic/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_proof_of_purchase(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_proof_of_purchase/bundle.mthds",
                "-i",
                "examples/b_basics/document_extract/extract_proof_of_purchase/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_table(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_table/bundle.mthds",
                "-i",
                "examples/b_basics/document_extract/extract_table/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_invoice_extractor(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "bundle",
                "examples/b_basics/document_extract/extract_invoice/bundle.mthds",
                "-i",
                "examples/b_basics/document_extract/extract_invoice/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    @pytest.mark.gha_disabled
    def test_hello_plugin(self, pipelex_cmd: str):
        if not get_optional_env("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is not set")
        else:
            result = subprocess.run(
                [pipelex_cmd, "run", "bundle", "examples/c_advanced/using_inference_plugins/hello_plugin.mthds"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Command failed: {result.stderr}"
