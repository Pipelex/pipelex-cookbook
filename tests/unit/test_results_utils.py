import os

from pytest_mock import MockerFixture

from utils.results_utils import (
    RESULTS_DIR_PATH,
    get_results_dir_path,
    get_results_file_path,
    output_result,
)


class TestResultsUtils:
    def test_get_results_dir_path(self, mocker: MockerFixture) -> None:
        """Test getting results directory path"""
        sample_name = "test_sample"
        expected_path = f"{RESULTS_DIR_PATH}/test_sample"

        # Mock get_incremental_directory_path
        mock_get_incremental_dir = mocker.patch("utils.results_utils.get_incremental_directory_path", return_value=expected_path)

        result = get_results_dir_path(sample_name)

        assert result == expected_path
        mock_get_incremental_dir.assert_called_once_with(
            base_path=RESULTS_DIR_PATH,
            base_name=sample_name,
        )

    def test_get_results_file_path(self, mocker: MockerFixture) -> None:
        """Test getting results file path"""
        sample_name = "test_sample"
        file_name = "test.txt"
        expected_dir_path = f"{RESULTS_DIR_PATH}/{sample_name}"
        expected_file_path = f"{expected_dir_path}/test_1.txt"

        # Mock ensure_path and get_incremental_file_path
        mock_ensure_path = mocker.patch("utils.results_utils.ensure_path")
        mock_get_incremental_file = mocker.patch("utils.results_utils.get_incremental_file_path", return_value=expected_file_path)

        result = get_results_file_path(sample_name, file_name)

        assert result == expected_file_path
        mock_ensure_path.assert_called_once_with(expected_dir_path)
        mock_get_incremental_file.assert_called_once_with(
            base_path=expected_dir_path,
            base_name="test",
            extension="txt",
        )

    def test_output_result(self, mocker: MockerFixture) -> None:
        """Test outputting result to file"""
        sample_name = "test_sample"
        title = "Test Title"
        file_name = "test.txt"
        content = "Test content"
        expected_file_path = f"{RESULTS_DIR_PATH}/{sample_name}/test_1.txt"

        # Mock get_results_file_path and save_text_to_path
        mock_get_results_file_path = mocker.patch("utils.results_utils.get_results_file_path", return_value=expected_file_path)
        mock_save_text = mocker.patch("utils.results_utils.save_text_to_path")
        mock_pretty_print = mocker.patch("utils.results_utils.pretty_print")

        output_result(sample_name, title, file_name, content)

        mock_get_results_file_path.assert_called_once_with(sample_name, file_name)
        mock_save_text.assert_called_once_with(content, expected_file_path)
        mock_pretty_print.assert_called_once_with(f"file://{os.path.abspath(expected_file_path)}", title=title)
