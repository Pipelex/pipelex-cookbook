domain = "gantt"
description = "The domain for gantt charts"
system_prompt = "You are an expert in gantt charts, you know all the different tricks, forms, traps"

[concept]
GanttTimescaleDescription = "Description of the timescale used in a specific gantt chart"
GanttTaskName = "Names of a task in a gantt chart"
GanttTaskDetails = "Task in a gantt chart"
GanttChart = "A gantt chart transcript fully detailing the contents of the chart"
GanttTranscript = "A gantt chart transcript fully detailing the contents of the chart in markdown format"

[concept.GanttChartImage]
description = "A gantt chart detailing a project timeline"
refines = "Image"

[pipe]
[pipe.extract_gantt_by_steps]
type = "PipeSequence"
description = "Extract all details from a gantt chart"
inputs = { gantt_chart_image = "GanttChartImage" }
output = "GanttChart"
steps = [
    { pipe = "extract_gantt_timescale", result = "gantt_timescale" },
    { pipe = "extract_gantt_task_names", result = "gantt_task_names" },
    { pipe = "extract_details_of_task", batch_over = "gantt_task_names", batch_as = "gantt_task_name", result = "details_of_all_tasks" },
    { pipe = "gather_in_a_gantt_chart", result = "gantt_chart" },
]

[pipe.extract_gantt_timescale]
type = "PipeLLM"
description = "Describe the timescale of a gantt chart"
inputs = { gantt_chart_image = "GanttChartImage" }
output = "GanttTimescaleDescription"
model = "llm_to_extract_diagram"
prompt = """
I am sharing an image of a Gantt chart: $gantt_chart_image.
Please analyze the timescale: what is the smallest unit detailed in the time scale?
"""

[pipe.extract_gantt_task_names]
type = "PipeLLM"
description = "List all the tasks"
inputs = { gantt_chart_image = "GanttChartImage" }
output = "GanttTaskName"
model = "llm_to_extract_diagram"
multiple_output = true
prompt = """
I am sharing an image of a Gantt chart: $gantt_chart_image.
Please analyse the image and list all the task names.
"""

[pipe.extract_details_of_task]
type = "PipeLLM"
description = "Extract the precise dates of the task, start_date and end_date"
inputs = { gantt_chart_image = "GanttChartImage", gantt_timescale = "GanttTimescaleDescription", gantt_task_name = "GanttTaskName" }
output = "GanttTaskDetails"
structuring_method = "preliminary_text"
model = "llm_to_extract_diagram"
prompt = """
I am sharing an image of a Gantt chart: $gantt_chart_image.
Please analyse the image and for a given task name (and only this task), extract the information of the task, if relevant.

Be careful, the time unit is this:
@gantt_timescale

If the task is a milestone, then only output the start_date.

Here is the name of the task you have to extract the dates for:
@gantt_task_name
"""

[pipe.gather_in_a_gantt_chart]
type = "PipeLLM"
description = "Gather all the tasks in a gantt chart"
inputs = { details_of_all_tasks = "GanttTaskDetails" }
output = "GanttChart"
prompt = """
Now you will receive all the necessary information to build a gantt chart.

Here are the task details:
@details_of_all_tasks
"""

########################################################
# Transcript direct in one go
########################################################

[pipe.transcript_gantt_direct]
type = "PipeLLM"
description = "Extract all details from a gantt chart"
inputs = { image = "GanttChartImage" }
output = "GanttTranscript"
model = "llm_to_extract_diagram"
prompt = """
# **Task:** You are provided with an image depicting a planning or timeline: $image.
Your objective is to produce a clear, comprehensive, and detailed description of the planning or timeline, focusing on its structure, events, and key details.

# **Requirements:**
 1. **Extract and list all dates** along with their corresponding events.
 2. **Highlight durations** and any additional relevant information included in the timeline.

# **Guidelines:**
 - Ensure there is no confusion between day dates and week numbers.
 - Avoid inventing or assuming dates that are not clearly presented.
 - Flag any dates or information that appear inaccurate, unclear, or challenging to extract.

# **Output:**
For each swimlane, extract the events and their corresponding dates from the Gantt chart image.
Either it's a sequence of punctual events, in that case output them like this:
- [swimlane title] (punctual): date1, date2, date3, ...

Or if it's a time interval, output it like this:
- [swimlane title] (interval): start_date to end_date

Additional events, if any, can be added like this (adapt to bullet point to the kind of timing used for each additional event):
- [additional label]: date

Use basic markdown to present this information in a clear and readable manner, like this:
```
# Gantt chart transcript

## Timescale
[simple and clear summary of the timescale units used, start and end date...]

## Swimlanes
[the list of swimlanes detailed using the format described above]

## Additional events
[the additional events if any]
```

No intro phrase is needed, no conclusion, and don't include ticks ``` or <xml> tags either, just the pure markdown.
"""

