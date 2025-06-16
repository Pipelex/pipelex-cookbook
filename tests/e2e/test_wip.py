import pytest


@pytest.mark.dry_runnable
class TestWip:
    def test_write_tweet(self):
        import examples.wip.write_tweet  # noqa: F401

    def test_write_screenplay(self):
        import examples.wip.write_screenplay  # noqa: F401
