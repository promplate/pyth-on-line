import type { PageLoad } from "./$types";

export const load = (async ({ fetch }) => {
  const sources: Record<string, string> = await fetch("").then(res => res.json());
  return { sources };
}) satisfies PageLoad;
