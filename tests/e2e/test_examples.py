import subprocess

import pytest
from pipelex.system.environment import get_optional_env


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestExamples:
    def test_extract_dpe(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_dpe/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_dpe/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_gantt(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_gantt/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_gantt/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_generic(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_generic/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_generic/inputs.json",
                "-L",
                "examples",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_proof_of_purchase(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_proof_of_purchase/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_proof_of_purchase/inputs.json",
                "-L",
                "examples/documents",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_extract_table(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_table/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_table/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_invoice_extractor(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/b_basics/document_extract/extract_invoice/bundle.plx",
                "-i",
                "examples/b_basics/document_extract/extract_invoice/inputs.json",
                "-L",
                "examples/documents",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    @pytest.mark.gha_disabled
    def test_hello_plugin(self):
        if not get_optional_env("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is not set")
        else:
            result = subprocess.run(
                ["pipelex", "run", "examples/c_advanced/using_inference_plugins/hello_plugin.plx"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Command failed: {result.stderr}"
