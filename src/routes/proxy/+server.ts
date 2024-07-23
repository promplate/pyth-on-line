import type { RequestHandler } from "./$types";

import { error } from "@sveltejs/kit";
import { get } from "$lib/utils/headers";

function getUrl(url: string | null) {
  if (!url) {
    error(400);
  }

  try {
    return new URL(url);
  }
  catch (e) {
    error(400, (e as Error).message);
  }
}

export const GET: RequestHandler = async ({ url: { searchParams }, request: { headers } }) => {
  const url = getUrl(searchParams.get("url"));

  return await get(url, headers);
};
