/**
 * Send a Gantt chart image from this machine to the hosted API through an upload grant, run the extraction on it,
 * and print every task and milestone it reads.
 *
 *     npm run extract -- ../../../../assets/extract_gantt/gantt_tree_house.png
 *
 * PIPELEX_API_KEY must be set; each chart is one run and spends credit.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

import { PipelexApiClient, uploadWithGrant } from "@pipelex/sdk";

import { parseGanttChart } from "./generated/extract_gantt/binder";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/extract_gantt@v0.18.0";
const IMAGE_TYPES: Record<string, string> = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };

const imagePath = process.argv[2];
const contentType = imagePath ? IMAGE_TYPES[path.extname(imagePath).toLowerCase()] : undefined;
if (!imagePath || !contentType) {
  console.error(`usage: npm run extract -- <image: ${Object.keys(IMAGE_TYPES).join(", ")}>`);
  process.exit(2);
}
const bytes = await readFile(imagePath);
const client = new PipelexApiClient();

// 1. The grant: the API names where this one file goes and the storage uri the method will read it from.
//    Only the side holding the API key can ask for one.
const grant = await client.requestUploadGrant({ filename: path.basename(imagePath), content_type: contentType, size: bytes.byteLength });

// 2. The bytes go straight to storage with the grant, not through the API. In a web app, the server asks for the
//    grant and the browser does this step, with `uploadWithGrant` from the browser-safe `@pipelex/sdk/upload`.
const { uri } = await uploadWithGrant(grant, new Blob([bytes], { type: contentType }));
console.error(`uploaded ${path.basename(imagePath)} as ${uri}`);

// 3. The run reads the image by its storage uri, given as the image's url.
const results = await client.startAndWaitForResult({ method_ref: METHOD_REF, inputs: { gantt_chart_image: { url: uri } } });
const chart = parseGanttChart(results.main_stuff);

for (const task of chart.tasks ?? []) {
  console.log(`${task.start_date ?? "?"} → ${task.end_date ?? "?"}  ${task.name}`);
}
for (const milestone of chart.milestones ?? []) {
  console.log(`◆ ${milestone.milestone_date ?? "?"}  ${milestone.name}`);
}
console.error(`${chart.tasks?.length ?? 0} task(s) and ${chart.milestones?.length ?? 0} milestone(s), run ${results.pipeline_run_id}`);
