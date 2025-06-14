import pytest
from pydantic import ValidationError


@pytest.mark.dry_runnable
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
