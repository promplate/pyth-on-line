import type { RequestHandler } from "./$types";

import { load } from "./+page.server";
import { error, json } from "@sveltejs/kit";

export const GET: RequestHandler = async ({ fetch, url: { searchParams } }) => {
  if (!searchParams.get("q")) {
    error(400, "Invalid query");
  }
  // @ts-expect-error missing parent, depends, untrack
  return json(await load({ fetch, url: { searchParams } }));
};
