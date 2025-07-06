import pytest
from pipelex.exceptions import PipeInputError, PipeLibraryPipeNotFoundError


@pytest.mark.dry_runnable
class TestWip:
    def test_write_tweet(self):
        import examples.wip.write_tweet  # noqa: F401

    @pytest.mark.xfail(raises=PipeLibraryPipeNotFoundError, reason="Requires new upcoming features to complete the pipeline")
    def test_write_screenplay(self):
        import examples.wip.write_screenplay  # noqa: F401
