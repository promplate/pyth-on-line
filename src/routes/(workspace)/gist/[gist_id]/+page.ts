import type { PageLoad } from "./$types";

import { error } from "@sveltejs/kit";

export const load = (async ({ fetch, url }) => {
  const res = await fetch(url.pathname);
  if (!res.ok)
    error(res.status, "Unable to load gist");
  const sources: Record<string, string> = await res.json();
  return { sources };
}) satisfies PageLoad;
