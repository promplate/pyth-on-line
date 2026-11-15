import type { RequestHandler } from "./$types";
import type { GistResponse } from "./common";

import { transformFiles } from "./common";
import { error, json } from "@sveltejs/kit";
import { forwardResponseHeaders } from "#lib/utils/headers.js";
import * as env from "$app/env/private";

export const GET: RequestHandler = async ({ params: { gist_id }, fetch, cookies }) => {
  const token = cookies.get("access_token") || env.GITHUB_TOKEN;
  const headers = new Headers();
  token && headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`https://api.github.com/gists/${gist_id}`, { headers });
  if (!res.ok)
    error(res.status, "Unable to load gist");
  const { files }: GistResponse = await res.json();
  return json(transformFiles(files), { headers: forwardResponseHeaders(res.headers) });
};
