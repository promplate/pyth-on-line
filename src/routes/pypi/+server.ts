import type { RequestHandler } from "./$types";

import { load } from "./+page.server";
import { error, json } from "@sveltejs/kit";

export const GET: RequestHandler = async ({ fetch, url: { searchParams } }) => {
  if (!searchParams.has("q")) {
    error(400, "Missing query parameter 'q'");
  }
  // @ts-expect-error missing parent, depends, untrack
  return json(await load({ fetch, url: { searchParams } }));
};
