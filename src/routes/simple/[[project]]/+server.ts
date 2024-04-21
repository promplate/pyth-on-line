import type { RequestHandler } from "./$types";

import { json } from "@sveltejs/kit";

export const GET: RequestHandler = async ({ params: { project }, request }) => {
  const host = new URL(request.url).origin;
  const res: { files: { url: string }[] } = await fetch(`https://pypi.org/simple/${project ?? ""}`, { headers: { accept: "application/vnd.pypi.simple.v1+json" } }).then(r => r.json());
  return json(project ? { ...res, files: res.files.map(f => ({ ...f, url: f.url.replace("https://files.pythonhosted.org", host) })) } : res, { headers: { "content-type": "application/vnd.pypi.simple.v1+json" } });
};

export const trailingSlash = "ignore";
