import os

from pipelex import pretty_print
from pipelex.tools.misc.file_utils import (
    ensure_path,
    get_incremental_directory_path,
    get_incremental_file_path,
    save_text_to_path,
)

RESULTS_DIR_PATH = "results/examples"


def get_results_dir_path(sample_name: str):
    result_dir_path = get_incremental_directory_path(
        base_path=RESULTS_DIR_PATH,
        base_name=sample_name,
    )
    return result_dir_path


def get_results_file_path(sample_name: str, file_name: str):
    extension = file_name.split(".")[-1]
    base_name = file_name.split(".")[0]
    result_dir_path = f"{RESULTS_DIR_PATH}/{sample_name}"
    ensure_path(result_dir_path)
    result_file_path = get_incremental_file_path(
        base_path=result_dir_path,
        base_name=base_name,
        extension=extension,
    )
    return result_file_path


def output_result(
    sample_name: str,
    title: str,
    file_name: str,
    content: str,
):
    result_file_path = get_results_file_path(sample_name, file_name)
    save_text_to_path(content, result_file_path)
    pretty_print(f"file://{os.path.abspath(result_file_path)}", title=title)
