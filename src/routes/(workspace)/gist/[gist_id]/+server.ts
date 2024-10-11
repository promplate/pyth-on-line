import type { RequestHandler } from "./$types";

import { type GistResponse, transformFiles } from "./common";
import { json } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";
import { forwardResponseHeaders } from "$lib/utils/headers";

export const GET: RequestHandler = async ({ params: { gist_id }, fetch, cookies }) => {
  const token = cookies.get("access_token") || env.GITHUB_TOKEN;
  const headers = new Headers();
  token && headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`https://api.github.com/gists/${gist_id}`, { headers });
  const { files }: GistResponse = await res.json();
  return json(transformFiles(files), { headers: forwardResponseHeaders(res.headers) });
};
