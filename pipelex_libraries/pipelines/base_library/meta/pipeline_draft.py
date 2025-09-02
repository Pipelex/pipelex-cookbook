from typing import Dict

from pipelex.core.bundles.pipelex_bundle_blueprint import PipelexBundleBlueprint
from pipelex.core.stuffs.stuff_content import StructuredContent
from pydantic import Field


class PipeDraft(StructuredContent):
    code: str
    type: str
    definition: str
    inputs: Dict[str, str]
    output: str


class PipelineDraft(StructuredContent):
    """Complete blueprint of a pipeline library PLX file."""

    # Domain information (required)
    domain: str
    definition: str

    # Concepts section - concept_name -> definition (string) or blueprint (dict)
    concept: Dict[str, str] = Field(default_factory=dict)

    # Pipes section - pipe_name -> blueprint dict
    pipe: Dict[str, PipeDraft] = Field(default_factory=dict)


class PipelexBundleBlueprintStuff(PipelexBundleBlueprint, StructuredContent):
    """Complete blueprint of a pipelex bundle PLX file."""

    pass
