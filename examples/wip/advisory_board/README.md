# Advisory Board Orchestrator

A sophisticated multi-advisory board consultation system that analyzes complex business problems by leveraging multiple domain expert perspectives.

## Run the pipeline

```bash
pipelex run examples/wip/advisory_board/advisory_orchestrator.plx -i examples/wip/advisory_board/inputs.json
```

## Expected output

![Expected output](expected_output.png)

## Flowchart

<!-- Pipeline flowchart will be added here -->

---

## What it Does

The Advisory Board Orchestrator:
1. **Analyzes** a business problem and classifies it into a structured format
2. **Selects** the most relevant advisory boards from 16+ available boards based on the problem type
3. **Consults** each selected board to get domain-specific recommendations
4. **Synthesizes** all responses to identify consensus, conflicts, and unique insights
5. **Generates** a comprehensive strategic report with actionable recommendations

## Key Features Demonstrated

- **Complex Pipeline Orchestration**: Uses `PipeSequence` with multiple steps
- **Batch Processing**: Consults multiple advisory boards in parallel using `batch_over`
- **Structured Output**: Generates typed outputs using inline PLX structures
- **Multi-Perspective Analysis**: Synthesizes diverse expert opinions
- **Conflict Resolution**: Identifies and provides frameworks for resolving conflicting advice

## Available Advisory Boards

The system can consult boards including:
- Executive Leadership
- Product Management
- Go-to-Market (GTM)
- Engineering & Technology
- Customer Success & Support
- Finance & Corporate Development
- And 10+ more specialized boards

Each board provides domain-specific analysis and recommendations based on their expertise area.
