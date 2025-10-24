domain = "synthetic_data_generation"
description = """
Generating synthetic data profiles from descriptions by identifying sample cases and creating profiles for each case.
"""
main_pipe = "generate_synthetic_data_profiles"

[concept]
SampleCaseCharacterization = "A concise one-sentence description characterizing a scenario, case, person or situation that should be covered as a sample."

[concept.DataDescription]
description = """
A specification of the synthetic data to be produced, including its purpose, structure, and characteristics.
"""
refines = "Text"


[concept.Sample]
description = "A complete synthetic data record representing a specific sample case."
refines = "Text"

[pipe.generate_synthetic_data_profiles]
type = "PipeSequence"
description = """
Main pipeline that orchestrates the entire synthetic data generation process. Takes a description of the synthetic data to produce, first identifies a comprehensive variety of sample cases that cover all expected real-world scenarios, then creates detailed synthetic data profiles for each identified case. This is the entry point for the complete synthetic data generation workflow.
"""
inputs = { data_description = "DataDescription" }
output = "Sample[]"
steps = [
    { pipe = "identify_sample_cases", result = "sample_cases" },
    { pipe = "create_profile_for_case", result = "profiles", batch_over = "sample_cases", batch_as = "sample_case_characterization" },
]

[pipe.identify_sample_cases]
type = "PipeLLM"
description = """
Analyzes the data description and generates a comprehensive list of real-world sample cases that should be covered in the synthetic data generation. Each case is characterized by a single concise sentence that captures a distinct scenario or situation. The LLM considers edge cases, common scenarios, and variations to ensure comprehensive coverage of all expected real-world situations.
"""
inputs = { data_description = "DataDescription" }
output = "SampleCaseCharacterization[]"
model = "llm_for_creative_writing"
system_prompt = """
You are an expert at analyzing data requirements and identifying comprehensive sample cases for synthetic data generation. Your task is to generate a list of SampleCaseCharacterization structured objects that cover diverse real-world scenarios, including common cases, edge cases, and important variations.
"""
prompt = """
Based on the following data description, generate a comprehensive list of real-world sample cases that should be covered in the synthetic data generation.

@data_description

Consider:
- Common, typical scenarios
- Edge cases and boundary conditions
- Important variations and diversity
- Real-world situations that would test the data's completeness

Generate a diverse set of sample cases to ensure comprehensive coverage of all expected situations.
"""


[pipe.create_profile_for_case]
type = "PipeLLM"
description = """
Creates a detailed synthetic data profile for a single sample case. Takes the original data description and a specific case characterization, then generates a complete synthetic data record that matches both the overall data specification and the specific characteristics of the sample case. The profile is a fully realized data instance ready for use.
"""
inputs = { data_description = "DataDescription", sample_case_characterization = "SampleCaseCharacterization" }
output = "Profile"
model = "llm_for_creative_writing"
system_prompt = """
You are a synthetic data generator. Your task is to create a complete, realistic Profile that adheres to the given data specification while embodying the specific characteristics of the sample case provided.
"""
prompt = """
Generate a complete synthetic data profile based on the following specifications:

@data_description

The profile should specifically represent this sample case:
@sample_case_characterization

Create a fully realized, realistic data record that satisfies both the overall data specification and the specific characteristics of this case.
"""
