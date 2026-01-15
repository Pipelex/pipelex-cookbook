import asyncio

from pipelex.core.stuffs.list_content import ListContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.json_utils import load_json_dict_from_path

from examples.c_advanced.gen_synthetic_data.synth_struct import Sample
from examples.constants import LIBRARY_DIRS
from utils.results_utils import output_result

SAMPLE_NAME = "synthesize"


async def run_generate_synthetic_data_samples() -> ListContent[Sample]:
    inputs = load_json_dict_from_path("examples/c_advanced/gen_synthetic_data/inputs.json")
    pipe_output = await execute_pipeline(
        pipe_code="generate_synthetic_data_samples",
        inputs=inputs,
    )
    return pipe_output.main_stuff_as_list(item_type=Sample)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # Run the pipeline
        samples = asyncio.run(run_generate_synthetic_data_samples())

        output_result(
            sample_name=SAMPLE_NAME,
            title="Synthetic data",
            file_name="synthetic_data.json",
            content=samples.rendered_json(),
        )
