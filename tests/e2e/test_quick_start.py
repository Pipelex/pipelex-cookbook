import runpy

import pytest

from examples._quick_start import hello_world, simple_ocr, summarize_1_structured, summarize_2_steps


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestQuickStart:
    def test_hello_world(self):
        runpy.run_path(hello_world.__file__, run_name="__main__")

    def test_summarize_1_structured(self):
        runpy.run_path(summarize_1_structured.__file__, run_name="__main__")

    def test_summarize_2_steps(self):
        runpy.run_path(summarize_2_steps.__file__, run_name="__main__")

    def test_simple_ocr(self):
        runpy.run_path(simple_ocr.__file__, run_name="__main__")
