from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import Field


class Sample(StructuredContent):
    """A complete synthetic data record representing a student profile."""

    student_name: str = Field(description="The name of the student")

    # Basic Info
    current_performance: str = Field(
        description="The student's current performance level", json_schema_extra={"choices": ["Struggling", "Average", "Advanced"]}
    )

    # Learning Style
    learns_best_with: str = Field(
        description="The learning modality that works best for this student",
        json_schema_extra={"choices": ["Visual examples", "Step-by-step text", "Hands-on practice", "Videos"]},
    )
    pace: str = Field(description="The student's learning pace", json_schema_extra={"choices": ["Needs more time", "Normal", "Fast learner"]})
    complexity: str = Field(
        description="The level of complexity the student prefers",
        json_schema_extra={"choices": ["Prefers simple explanations", "Balanced", "Likes deep details"]},
    )

    # Background
    strengths: str = Field(description="Subjects or topics the student is good at")
    needs_help_with: str = Field(description="Areas where the student struggles")
    prior_knowledge: str = Field(description="Relevant topics the student already knows")

    # Interests
    hobbies_interests: str = Field(description="The student's hobbies and interests (e.g., soccer, video games, music)")
    career_goals: str = Field(description="The student's career aspirations (e.g., engineer, doctor, undecided)")

    # Preferences
    example_style: str = Field(
        description="The student's preferred example style", json_schema_extra={"choices": ["Many real-world examples", "Abstract concepts", "Mix"]}
    )
    question_format: str = Field(
        description="The student's preferred question format", json_schema_extra={"choices": ["Multiple choice", "Short answer", "Open discussion"]}
    )
