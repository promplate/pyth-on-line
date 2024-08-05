import * as env from "$env/static/public";

export function getEnv() {
  return Object.fromEntries(Object.entries(env as Record<string, string>).map(([k, v]) => [k.replace("PUBLIC_", ""), v]));
}
