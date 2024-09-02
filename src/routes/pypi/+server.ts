import type { RequestHandler } from "./$types";

import { search } from "./search";
import { error, json } from "@sveltejs/kit";

export const GET: RequestHandler = async (event) => {
  if (!event.url.searchParams.get("q")) {
    error(400, "Invalid query");
  }
  return json(await search(event));
};
