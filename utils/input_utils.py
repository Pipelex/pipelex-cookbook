from typing import Optional

from pipelex.system.environment import get_optional_env
from pipelex.tools.misc.file_utils import failable_load_text_from_path


def optional_sample_text_from_path(filename: str) -> Optional[str]:
    """
    Loads a text file from the examples path if it exists.
    """
    examples_path = get_optional_env("SAMPLES_PATH")
    if examples_path is None:
        print(f"The examples path var `SAMPLES_PATH` is not defined in env, we won't use text from a file for '{filename}'")
        return None
    path = f"{examples_path}/{filename}"
    text = failable_load_text_from_path(path=path)
    if not text:
        print(f"No text file found at'{path}'")
        return None
    print(f"Loaded text from '{path}'")
    return text
