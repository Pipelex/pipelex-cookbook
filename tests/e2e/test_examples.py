import pytest
from pipelex.tools.environment import get_optional_env


@pytest.mark.dry_runnable
@pytest.mark.gha_disabled
class TestExamples:
    def test_extract_dpe(self):
        import examples.extract_dpe  # noqa: F401

    def test_extract_gantt(self):
        import examples.extract_gantt  # noqa: F401

    def test_extract_generic(self):
        import examples.extract_generic  # noqa: F401

    def test_extract_proof_of_purchase(self):
        import examples.extract_proof_of_purchase  # noqa: F401

    def test_extract_table(self):
        import examples.extract_table  # noqa: F401

    def test_invoice_extractor(self):
        import examples.invoice_extractor  # noqa: F401

    def test_simple_ocr(self):
        import examples.simple_ocr  # noqa: F401

    def test_advisory_board(self):
        import examples.wip.advisory_board  # noqa: F401

    @pytest.mark.gha_disabled
    def test_hello_plugin(self):
        if not get_optional_env("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is not set")
        else:
            import examples.using_inference_plugins.hello_plugin  # noqa: F401
