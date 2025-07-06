# Master Advisory Orchestrator Example

This example demonstrates how to use the Master Advisory Orchestrator pipeline to analyze complex business problems and generate comprehensive strategic recommendations by consulting multiple expert advisory boards.

## Overview

The Master Advisory Orchestrator system:

1. **Structures business problems** - Converts raw problem descriptions into structured analysis
2. **Selects relevant advisory boards** - Chooses 5-10 expert boards from 16 available types based on problem characteristics
3. **Generates expert consultations** - Creates responses from multiple advisory perspectives in parallel
4. **Analyzes responses** - Identifies consensus points, conflicts, and unique insights
5. **Produces strategic reports** - Generates comprehensive recommendations with implementation roadmaps

## Available Advisory Boards

The system can consult the following expert advisory boards:

- **Executive Board** - Strategic leadership and organizational direction
- **Product Advisory Board** - Product strategy, roadmap, and market positioning
- **Go-to-Market Board** - Sales, marketing, and customer acquisition strategies
- **Engineering Board** - Technical architecture, development processes, and innovation
- **Operations Board** - Process optimization, scaling, and operational efficiency
- **Marketing Board** - Brand strategy, campaigns, and market positioning
- **Sales Board** - Revenue strategy, sales processes, and customer relationships
- **Finance Board** - Financial planning, investment, and risk management

And 8 additional specialized boards for specific domains.

## Usage

### Running the Example

```bash
cd examples
python run_advisory_orchestrator.py
```

### Sample Business Problem

The example includes a realistic business scenario:

> **B2B SaaS Customer Retention Crisis**
> 
> A mid-stage company ($5M ARR, 50 employees) facing declining retention:
> - Churn increased from 8% to 15% in 6 months
> - Slow onboarding (4-6 weeks vs 2-3 week industry average)
> - Poor support response times (24 hours)
> - Low feature adoption (30%)
> - New competitive pressure
> 
> **Goal:** Reduce churn to under 10% within 6 months with $500K budget

### Expected Output

The pipeline will generate:

1. **Structured Problem Analysis** - Categorized problem with context, constraints, and stakeholders
2. **Board Selection Strategy** - Chosen advisory boards with relevance scores and rationale
3. **Multi-Board Consultations** - Strategic analyses from each selected board
4. **Consensus Analysis** - Identified agreements, conflicts, and unique insights
5. **Strategic Report** - Executive summary, prioritized recommendations, implementation roadmap, risks, and success metrics

### Custom Business Problems

To analyze your own business problem, modify the `SAMPLE_BUSINESS_PROBLEM` variable in `run_advisory_orchestrator.py`:

```python
SAMPLE_BUSINESS_PROBLEM = """
Describe your business problem here including:
- Company context (size, stage, industry)
- Specific challenges and symptoms
- Goals and constraints
- Available resources
- Key stakeholders
"""
```

## Pipeline Architecture

### Main Sequence (5 Steps)

1. `classify_business_problem` - Converts text to structured BusinessProblem
2. `select_advisory_boards` - Chooses relevant expert boards
3. `consult_boards_parallel` - Generates responses from all selected boards
4. `analyze_board_responses` - Identifies patterns and conflicts
5. `generate_strategic_report` - Creates final strategic recommendations

### Key Features

- **Parallel Processing** - Multiple board consultations run simultaneously
- **Structured Data Flow** - Each step produces typed, structured outputs
- **Comprehensive Analysis** - Covers strategy, implementation, risks, and metrics
- **Flexible Board Selection** - Adapts expert mix based on problem characteristics

## Output Structure

### Strategic Report

```python
class StrategicReport(StructuredContent):
    executive_summary: str
    strategic_recommendations: List[StrategicRecommendation]
    implementation_roadmap: ImplementationRoadmap
    risk_assessment: RiskAssessment
    resource_requirements: ResourceRequirements
    success_metrics: List[SuccessMetric]
    next_steps: List[str]
```

### Performance Tracking

The example includes:
- **Cost reporting** - Token usage and LLM costs
- **Pipeline flowchart** - Visual representation of execution flow
- **Execution metrics** - Performance and timing data

## Requirements

- Pipelex framework installed
- Valid LLM API configuration
- Python 3.8+ with asyncio support

## Use Cases

This pipeline is ideal for:

- **Strategic planning** - Multi-perspective analysis of complex business challenges
- **Decision support** - Comprehensive evaluation of strategic options
- **Crisis management** - Rapid expert consultation for urgent business issues
- **Investment decisions** - Due diligence with multiple expert viewpoints
- **Market entry** - Cross-functional analysis of new opportunities

## Customization

### Adding New Advisory Boards

1. Update the board selection logic in `select_advisory_boards` pipe
2. Add corresponding consultation logic in individual board pipes
3. Update the `BoardType` enum in the structure classes

### Modifying Analysis Depth

- Adjust prompt templates for deeper or lighter analysis
- Modify the number of selected boards (currently 5-10)
- Customize success metrics and KPI definitions

### Integration Options

- **API Integration** - Expose as REST endpoint for web applications
- **Batch Processing** - Process multiple problems simultaneously
- **Custom Workflows** - Integrate specific steps into existing business processes 