import pytest


@pytest.mark.dry_runnable
class TestQuickStart:
    def test_hello_world(self):
        import examples._quick_start.hello_world  # noqa: F401

    def test_summarize_1_structured(self):
        import examples._quick_start.summarize_1_structured  # noqa: F401

    def test_summarize_2_steps(self):
        import examples._quick_start.summarize_2_steps  # noqa: F401

    def test_simple_ocr(self):
        import examples._quick_start.simple_ocr  # noqa: F401
