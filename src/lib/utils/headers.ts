const excludeRequestHeaders = ["authorization", "host", "origin"];
const excludeResponseHeaders = ["www-authenticate", "content-encoding", "content-length", "connection", "transfer-encoding", "keep-alive"];

export function forwardRequestHeaders(headersIn: Headers) {
  const headers = new Headers();
  headersIn.forEach((value, key) => {
    if (!excludeRequestHeaders.includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}

export function forwardResponseHeaders(headersIn: Headers) {
  const headers = new Headers();
  headersIn.forEach((value, key) => {
    if (!excludeResponseHeaders.includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}

export async function forwardFetch(url: string | URL, request: Request) {
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  const res = await fetch(url, { body, method: request.method, headers: forwardRequestHeaders(new Headers(request.headers)) });
  return new Response(res.body, { headers: forwardResponseHeaders(res.headers), status: res.status, statusText: res.statusText });
}
