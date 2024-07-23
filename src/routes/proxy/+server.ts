import type { RequestHandler } from "./$types";

import { error } from "@sveltejs/kit";

const excludeRequestHeaders = ["authorization", "host", "origin"];
const excludeResponseHeaders = ["www-authenticate", "content-encoding", "content-length", "connection", "transfer-encoding", "keep-alive"];

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

export const GET: RequestHandler = async ({ fetch, url: { searchParams }, request: { headers: reqHeaders } }) => {
  const url = getUrl(searchParams.get("url"));

  const headers = new Headers();

  for (const [key, value] of reqHeaders) {
    if (!excludeRequestHeaders.includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  }

  const res = await fetch(url, { headers });

  const resHeaders = new Headers();
  for (const [key, value] of res.headers) {
    if (!excludeResponseHeaders.includes(key.toLowerCase())) {
      resHeaders.set(key, value);
    }
  }

  return new Response(res.body, { headers: resHeaders, status: res.status, statusText: res.statusText });
};
