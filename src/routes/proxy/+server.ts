import type { RequestHandler } from "./$types";

import { error } from "@sveltejs/kit";
import { forwardFetch } from "$lib/utils/headers";

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

const handler: RequestHandler = async ({ url: { searchParams }, request }) => {
  const url = getUrl(searchParams.get("url"));
  if ([location.hostname, "localhost", "127.0.0.1", "::1"].includes(url.hostname))
    error(400, "Invalid hostname");
  return await forwardFetch(url, request);
};

export const GET = handler;
export const HEAD = handler;
export const PUT = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
