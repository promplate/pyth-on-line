import type { PageLoad } from "./$types";

import { error } from "@sveltejs/kit";

export const load = (async ({ fetch, url }) => {
  const res = await fetch(url.pathname);
  const sources: Record<string, string> = await res.json();
  if (!res.ok)
    error(res.status, sources.message);
  return { sources };
}) satisfies PageLoad;
