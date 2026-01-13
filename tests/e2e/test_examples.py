import runpy

import pytest
from pipelex.system.environment import get_optional_env

from examples.extract_dpe import extract_dpe
from examples.extract_gantt import extract_gantt
from examples.extract_generic import extract_generic
from examples.extract_invoice import extract_invoice
from examples.extract_proof_of_purchase import extract_proof_of_purchase
from examples.extract_table import extract_table
from examples.using_inference_plugins import hello_plugin
from examples.wip.advisory_board import advisory_board


@pytest.mark.dry_runnable
class TestExamples:
    def test_extract_dpe(self):
        runpy.run_path(extract_dpe.__file__, run_name="__main__")

    def test_extract_gantt(self):
        runpy.run_path(extract_gantt.__file__, run_name="__main__")

    def test_extract_generic(self):
        runpy.run_path(extract_generic.__file__, run_name="__main__")

    def test_extract_proof_of_purchase(self):
        runpy.run_path(extract_proof_of_purchase.__file__, run_name="__main__")

    def test_extract_table(self):
        runpy.run_path(extract_table.__file__, run_name="__main__")

    def test_invoice_extractor(self):
        runpy.run_path(extract_invoice.__file__, run_name="__main__")

    def test_advisory_board(self):
        runpy.run_path(advisory_board.__file__, run_name="__main__")

    @pytest.mark.gha_disabled
    def test_hello_plugin(self):
        if not get_optional_env("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is not set")
        else:
            runpy.run_path(hello_plugin.__file__, run_name="__main__")
