import type { PageLoad } from "./$types";

import { error } from "@sveltejs/kit";

export const load: PageLoad = async ({ fetch, url }) => {
  const response = await fetch(url.pathname, { headers: { accept: "application/json" } });
  if (!response.ok)
    error(response.status, (await response.json()).message);
  return { payload: await response.json() };
};
