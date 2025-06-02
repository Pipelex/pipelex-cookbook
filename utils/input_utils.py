from typing import Optional

from pipelex import log
from pipelex.tools.environment import get_optional_env
from pipelex.tools.misc.file_utils import failable_load_text_from_path


def optional_sample_text_from_path(filename: str) -> Optional[str]:
    """
    Loads a text file from the samples path if it exists.
    """
    samples_path = get_optional_env("SAMPLES_PATH")
    if samples_path is None:
        log.info(f"The samples path var `SAMPLES_PATH` is not defined in env, we won't use text from a file for '{filename}'")
        return None
    path = f"{samples_path}/{filename}"
    text = failable_load_text_from_path(path=path)
    if not text:
        log.info(f"No text file found at'{path}'")
        return None
    log.info(f"Loaded text from '{path}'")
    return text
