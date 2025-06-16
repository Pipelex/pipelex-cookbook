from pytest_mock import MockerFixture

from utils.input_utils import optional_sample_text_from_path


class TestInputUtils:
    def test_optional_sample_text_no_env(self, mocker: MockerFixture) -> None:
        """Test when SAMPLES_PATH environment variable is not set"""
        # Mock get_optional_env to return None
        mocker.patch("utils.input_utils.get_optional_env", return_value=None)

        result = optional_sample_text_from_path("test.txt")
        assert result is None

    def test_optional_sample_text_file_not_found(self, mocker: MockerFixture) -> None:
        """Test when SAMPLES_PATH is set but file doesn't exist"""
        # Mock get_optional_env to return a path
        mocker.patch("utils.input_utils.get_optional_env", return_value="/test/path")
        # Mock failable_load_text_from_path to return None (file not found)
        mocker.patch("utils.input_utils.failable_load_text_from_path", return_value=None)

        result = optional_sample_text_from_path("test.txt")
        assert result is None

    def test_optional_sample_text_success(self, mocker: MockerFixture) -> None:
        """Test when SAMPLES_PATH is set and file exists with content"""
        test_path = "/test/path"
        test_content = "Hello, World!"

        # Mock get_optional_env to return a path
        mocker.patch("utils.input_utils.get_optional_env", return_value=test_path)
        # Mock failable_load_text_from_path to return content
        mocker.patch("utils.input_utils.failable_load_text_from_path", return_value=test_content)

        result = optional_sample_text_from_path("test.txt")
        assert result == test_content
