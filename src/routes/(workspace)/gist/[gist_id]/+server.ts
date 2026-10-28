import type { RequestHandler } from "./$types";
import type { GistResponse } from "./common";

import { transformFiles } from "./common";
import { json } from "@sveltejs/kit";
import { forwardResponseHeaders } from "#lib/utils/headers.js";
import * as env from "$app/env/private";

export const GET: RequestHandler = async ({ params: { gist_id }, fetch, cookies }) => {
  const token = cookies.get("access_token") || env.GITHUB_TOKEN;
  const headers = new Headers();
  token && headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`https://api.github.com/gists/${gist_id}`, { headers });
  const { files }: GistResponse = await res.json();
  return json(transformFiles(files), { headers: forwardResponseHeaders(res.headers) });
};
