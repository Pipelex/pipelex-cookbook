from typing import Dict, List, Optional

from pipelex.core.stuffs.structured_content import StructuredContent
from pipelex.types import StrEnum
from pydantic import Field


class ProblemCategory(StrEnum):
    PRODUCT_LAUNCH = "product_launch"
    SCALING = "scaling"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    MARKETING = "marketing"
    GENERAL = "general"


class BusinessProblem(StructuredContent):
    problem_statement: str = Field(..., description="Clear statement of the business challenge")
    context: str = Field(..., description="Relevant business context and background")
    constraints: List[str] = Field(default_factory=list, description="Known limitations and constraints")
    goals: List[str] = Field(default_factory=list, description="Desired outcomes and objectives")
    category: ProblemCategory = Field(..., description="Primary category of the problem")
    urgency: str = Field(..., description="Timeline urgency (immediate, short-term, long-term)")
    stakeholders: List[str] = Field(default_factory=list, description="Key stakeholders involved")


class AdvisoryBoard(StructuredContent):
    name: str = Field(..., description="Name of the advisory board")
    expertise: str = Field(..., description="Domain expertise and perspective")
    relevance_score: float = Field(..., description="Relevance score for the problem (0-10)")
    selection_rationale: str = Field(..., description="Why this board was selected")


class ConsensusItem(StructuredContent):
    recommendation: str = Field(..., description="The consensus recommendation")
    supporting_boards: List[str] = Field(..., description="Boards that support this recommendation")
    confidence_score: float = Field(..., description="Confidence score (1-10)")
    priority: str = Field(..., description="Priority level (high, medium, low)")


class ConflictItem(StructuredContent):
    issue: str = Field(..., description="The conflicting issue")
    board_a_position: str = Field(..., description="Position of first board")
    board_b_position: str = Field(..., description="Position of second board")
    core_tension: str = Field(..., description="Root cause of the disagreement")
    decision_framework: str = Field(..., description="Framework for making the decision")
    compromise_option: Optional[str] = Field(None, description="Potential middle ground solution")


class ResponseAnalysis(StructuredContent):
    consensus_items: List[ConsensusItem] = Field(..., description="Areas of consensus across boards")
    conflicts: List[ConflictItem] = Field(..., description="Areas of conflicting advice")
    unique_insights: List[str] = Field(..., description="Unique perspectives from individual boards")
    dependencies: List[str] = Field(..., description="Cross-functional dependencies identified")
    resource_overlaps: List[str] = Field(..., description="Competing resource requirements")


class ImplementationPhase(StructuredContent):
    phase_name: str = Field(..., description="Name of the implementation phase")
    timeline: str = Field(..., description="Timeline for this phase")
    actions: List[str] = Field(..., description="Specific actions to take")
    lead_responsibility: List[str] = Field(..., description="Who leads each action")
    deliverables: List[str] = Field(..., description="Expected deliverables")


class RiskItem(StructuredContent):
    risk: str = Field(..., description="Description of the risk")
    severity: str = Field(..., description="Risk severity (high, medium, low)")
    mitigation: str = Field(..., description="Mitigation strategy")
    owner: str = Field(..., description="Who owns the risk mitigation")


class SuccessMetric(StructuredContent):
    metric: str = Field(..., description="The success metric")
    target: str = Field(..., description="Target value or outcome")
    measurement_method: str = Field(..., description="How to measure this metric")
    review_frequency: str = Field(..., description="How often to review")


class ResourceRequirement(StructuredContent):
    category: str = Field(..., description="Resource category (budget, personnel, technology)")
    description: str = Field(..., description="Detailed description of the requirement")
    quantity: str = Field(..., description="Quantity or amount needed")
    timeline: str = Field(..., description="When this resource is needed")


class StrategicReport(StructuredContent):
    executive_summary: str = Field(..., description="Executive summary of the analysis")
    problem_statement: str = Field(..., description="Restated problem statement")
    boards_consulted: List[str] = Field(..., description="List of advisory boards consulted")
    top_consensus_recommendations: List[str] = Field(..., description="Top 3 consensus recommendations")
    critical_decision_points: List[str] = Field(..., description="Areas requiring leadership choice")

    consensus_recommendations: List[ConsensusItem] = Field(..., description="High consensus recommendations")
    strategic_choices: List[ConflictItem] = Field(..., description="Strategic choices requiring decisions")
    domain_insights: Dict[str, str] = Field(..., description="Key insights by domain")

    implementation_phases: List[ImplementationPhase] = Field(..., description="Phased implementation roadmap")
    risks: List[RiskItem] = Field(..., description="Risk assessment and mitigation")
    resource_requirements: List[ResourceRequirement] = Field(..., description="Resource requirements summary")
    success_metrics: List[SuccessMetric] = Field(..., description="Success metrics dashboard")

    next_steps: List[str] = Field(..., description="Immediate next steps")
    review_schedule: str = Field(..., description="Recommended review and assessment schedule")
