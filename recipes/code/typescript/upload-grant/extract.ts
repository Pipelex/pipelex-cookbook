/**
 * Send a French energy performance diagnostic (DPE) from this machine to the hosted API through an upload grant, run the
 * extraction on it, and print the record it reads.
 *
 *     npm run extract -- ../../../../assets/extract_dpe/synthetic_dpe.pdf
 *
 * PIPELEX_API_KEY must be set; each diagnostic is one run and spends credit.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

import { PipelexApiClient, uploadWithGrant } from "@pipelex/sdk";

import { parseDpeRecord } from "./generated/extract_dpe/binder";

const METHOD_REF = "github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.20.0";
const CONTENT_TYPE = "application/pdf";

const documentPath = process.argv[2];
if (!documentPath || path.extname(documentPath).toLowerCase() !== ".pdf") {
  console.error("usage: npm run extract -- <a DPE as a PDF>");
  process.exit(2);
}
const bytes = await readFile(documentPath);
const client = new PipelexApiClient();

// 1. The grant: the API names where this one file goes and the storage uri the method will read it from.
//    Only the side holding the API key can ask for one.
const grant = await client.requestUploadGrant({ filename: path.basename(documentPath), content_type: CONTENT_TYPE, size: bytes.byteLength });

// 2. The bytes go straight to storage with the grant, not through the API. In a web app, the server asks for the
//    grant and the browser does this step, with `uploadWithGrant` from the browser-safe `@pipelex/sdk/upload`.
const { uri } = await uploadWithGrant(grant, new Blob([bytes], { type: CONTENT_TYPE }));
console.error(`uploaded ${path.basename(documentPath)} as ${uri}`);

// 3. The run reads the document by its storage uri, given as the document's url.
const results = await client.startAndWaitForResult({ method_ref: METHOD_REF, inputs: { document: { url: uri } } });
const record = parseDpeRecord(results.main_stuff);

const prices = record.energy_prices_as_of ? `, at the prices of ${record.energy_prices_as_of}` : "";
console.log(`Address       ${record.address}`);
console.log(`DPE number    ${record.dpe_number}`);
console.log(`Valid         ${record.date_of_issue} → ${record.date_of_expiration}`);
console.log(`Energy class  ${record.energy_efficiency_class}, ${record.per_year_per_m2_consumption} kWh/m²/year`);
console.log(`CO₂ class     ${record.co2_emission_class}, ${record.per_year_per_m2_co2_emissions} kg/m²/year`);
console.log(`Energy costs  ${record.yearly_energy_costs_min} to ${record.yearly_energy_costs_max} € a year${prices}`);
console.log(`Letting       ${record.letting_status}`);
console.error(`run ${results.pipeline_run_id}`);
