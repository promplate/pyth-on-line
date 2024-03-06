import * as env from "$env/static/public";

export function getEnv() {
  return Object.fromEntries(Object.entries(env).map(([k, v]) => [k.replace("PUBLIC_", ""), v]));
}
