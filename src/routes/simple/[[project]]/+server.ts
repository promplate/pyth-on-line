import type { RequestHandler } from "./$types";

import { error, json } from "@sveltejs/kit";

export const GET: RequestHandler = async ({ params: { project }, request }) => {
  const host = new URL(request.url).origin;
  const response = await fetch(`https://pypi.org/simple/${project ?? ""}`, { headers: { accept: "application/vnd.pypi.simple.v1+json" } });
  if (!response.ok)
    error(response.status, response.status === 404 ? "Package not found" : "Unable to load package index");
  const res: { files: { url: string }[] } = await response.json();
  return json(project ? { ...res, files: res.files.map(f => ({ ...f, url: f.url.replace("https://files.pythonhosted.org", host) })) } : res, { headers: { "content-type": "application/vnd.pypi.simple.v1+json" } });
};

export const trailingSlash = "ignore";
