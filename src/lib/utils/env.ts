import * as env from "$app/env/public";

export function getEnv() {
  // Kit declares optional variables even when absent; Pyodide's ENV only accepts strings.
  return Object.fromEntries(Object.entries(env).filter((entry): entry is [string, string] => entry[1] !== undefined).map(([k, v]) => [k.replace("PUBLIC_", ""), v]));
}
