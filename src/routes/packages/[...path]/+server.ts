import type { RequestHandler } from "./$types";

export const GET: RequestHandler = async ({ request }) => {
  const host = new URL(request.url).origin;
  const url = request.url.replace(host, "https://files.pythonhosted.org");
  const res = await fetch(url);

  const headers: HeadersInit = {};

  res.headers.forEach((value, key) => {
    if (key.startsWith("access-control-") || key.startsWith("x-"))
      headers[key] = value;
  });

  return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
};
