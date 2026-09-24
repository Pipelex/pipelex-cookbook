# Key: gantt_tree_house

Inputs: `assets/extract_gantt/gantt_tree_house.png`, the Gantt chart of a tree-house build titled "Forest Animals Tree House Construction", drawn at a daily scale from Monday 1 September to Tuesday 14 October 2025, with twelve numbered tasks and a row of five milestones. It is the sample the example has always shipped with.

## Planted facts
F1. The subtitle gives the project timeline as September 1, 2025 to October 11, 2025.
F2. The twelve task bars span: 1. Planning & Design, 1 to 8 September; 2. Resource Gathering, 5 to 10 September; 3. Site Preparation, 7 to 10 September; 4. Foundation & Supports, 11 to 15 September; 5. Platform Construction, 15 to 18 September; 6. Frame & Walls Construction, 19 to 25 September; 7. Roofing Installation, 24 to 29 September; 8. Windows & Doors Installation, 26 to 29 September; 9. Ladder Installation, 29 to 30 September; 10. Interior Setup, 1 to 6 October; 11. Inspections & Adjustments, 6 to 10 October; 12. Celebration Preparation, 8 to 11 October.
F3. The milestones row holds five diamonds: Blueprint on 8 September, Foundation on 15 September, Structure on 29 September, Interior on 6 October and Celebration on 11 October.
F4. Weekends are shaded, and several bars cross them: the chart counts calendar days, not working days.

## Must
M1. `tasks` holds the chart's twelve tasks, each named recognisably as on the chart, with or without its number.
M2. Each task's `start_date` and `end_date` are within one day of the chart's: Planning & Design from 1 to 8 September, Resource Gathering 5 to 10 September, Site Preparation 7 to 10 September, Foundation & Supports 11 to 15 September, Platform Construction 15 to 18 September, Frame & Walls Construction 19 to 25 September, Roofing Installation 24 to 29 September, Windows & Doors Installation 26 to 29 September, Ladder Installation 29 to 30 September, Interior Setup 1 to 6 October, Inspections & Adjustments 6 to 10 October, and Celebration Preparation 8 to 11 October.
M3. Every date is in 2025.
M4. `milestones` holds the five milestones Blueprint, Foundation, Structure, Interior and Celebration.
M5. Each milestone's `milestone_date` is within one day of the chart's: Blueprint on 8 September, Foundation on 15 September, Structure on 29 September, Interior on 6 October and Celebration on 11 October.

## Must not
N1. A milestone listed among `tasks`, or a task among `milestones`.
N2. A task whose `end_date` is before its `start_date`.
N3. A date in another year, or a day of the month read as a week number.
N4. The row label "Milestones" returned as a task or a milestone.

## Also acceptable
A1. A task's name keeping its number ("1. Planning & Design") or dropping it ("Planning & Design"), for M1.

## Pass bar
Every Must and Must not line.
