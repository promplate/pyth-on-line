import type { PageServerLoad } from "./$types";

import { redirect } from "@sveltejs/kit";
import { getOauthUrl } from "#lib/oauth.js";
import * as server from "$app/env/private";
import * as env from "$app/env/public";

// eslint-disable-next-line ts/ban-ts-comment
// @ts-ignore
const client_secret = server.GITHUB_CLIENT_SECRET;
// eslint-disable-next-line ts/ban-ts-comment
// @ts-ignore
const client_id = env.PUBLIC_GITHUB_CLIENT_ID;

export const load = (async ({ fetch, url: { searchParams, origin }, cookies }) => {
  const code = searchParams.get("code");
  if (!code) {
    redirect(308, getOauthUrl(origin), { external: true });
  }
  const { access_token } = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    body: JSON.stringify({ client_id, client_secret, code }),
    headers: { "accept": "application/json", "content-type": "application/json" },
  }).then(res => res.json());

  access_token && cookies.set("access_token", access_token, { path: "/", maxAge: 60 * 60 * 24 * 365 });

  return { access_token };
}) satisfies PageServerLoad;
