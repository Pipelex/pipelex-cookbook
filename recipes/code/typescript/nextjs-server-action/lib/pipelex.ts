import { PipelexApiClient } from "@pipelex/sdk";

let client: PipelexApiClient | undefined;

/**
 * One client for the whole server process, made on first use, reading `PIPELEX_API_KEY` from the server's environment.
 * Only server code imports this module, so the key never reaches the browser.
 */
export function pipelexClient(): PipelexApiClient {
  client ??= new PipelexApiClient();
  return client;
}
